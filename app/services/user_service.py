from app.models.user import User
from app.repositories.disaster_event import DisasterEventRepository
from app.repositories.saved_location import SavedLocationRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserAdminUpdate, UserDeleteRequest, UserSelfUpdate
from app.utilities.security import encrypt_password, verify_password


class UserValidationError(ValueError):
    pass


class UserConflictError(Exception):
    pass


class UserAuthorizationError(Exception):
    pass


class UserService:
    VALID_ROLES = {"admin", "regular_user"}

    def __init__(
        self,
        user_repo: UserRepository,
        saved_location_repo: SavedLocationRepository | None = None,
        disaster_repo: DisasterEventRepository | None = None,
    ):
        self.user_repo = user_repo
        self.saved_location_repo = saved_location_repo
        self.disaster_repo = disaster_repo

    def get_all_users(self):
        users = self.user_repo.get_all_users()
        return sorted(users, key=lambda user: (user.role != "admin", user.username.lower()))

    def get_user_by_id(self, user_id: int) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise LookupError("User not found.")
        return user

    def update_current_user(self, current_user: User, payload: UserSelfUpdate) -> User:
        changes = self._build_identity_changes(
            target_user=current_user,
            username=payload.username,
            email=payload.email,
        )

        if payload.current_password or payload.new_password:
            if not payload.current_password or not payload.new_password:
                raise UserValidationError("Provide both your current password and a new password.")
            if not verify_password(
                plaintext_password=payload.current_password,
                encrypted_password=current_user.password_hash,
            ):
                raise UserAuthorizationError("Current password is incorrect.")
            if payload.current_password == payload.new_password:
                raise UserValidationError("Choose a new password that differs from the current password.")
            changes["password_hash"] = encrypt_password(payload.new_password)

        if not changes:
            return current_user

        return self.user_repo.update_user(current_user, changes)

    def update_user_as_admin(self, acting_user: User, user_id: int, payload: UserAdminUpdate) -> User:
        target_user = self.get_user_by_id(user_id)
        if acting_user.id == target_user.id:
            raise UserAuthorizationError("Use your profile page to manage your own account.")

        changes = self._build_identity_changes(
            target_user=target_user,
            username=payload.username,
            email=payload.email,
        )

        if payload.role is not None:
            role = payload.role.strip()
            if role not in self.VALID_ROLES:
                raise UserValidationError("Role must be either admin or regular_user.")
            if target_user.role == "admin" and role != "admin":
                self._ensure_not_last_admin(target_user)
            changes["role"] = role

        if not changes:
            return target_user

        return self.user_repo.update_user(target_user, changes)

    def delete_current_user(self, current_user: User, payload: UserDeleteRequest) -> None:
        if payload.confirm_username.strip() != current_user.username:
            raise UserValidationError("Type your current username exactly to confirm account deletion.")
        if not verify_password(
            plaintext_password=payload.current_password,
            encrypted_password=current_user.password_hash,
        ):
            raise UserAuthorizationError("Current password is incorrect.")
        self._ensure_not_last_admin(current_user)
        self._delete_user_with_dependencies(current_user)

    def delete_user_as_admin(self, acting_user: User, user_id: int) -> None:
        target_user = self.get_user_by_id(user_id)
        if acting_user.id == target_user.id:
            raise UserAuthorizationError("Use your profile page to delete your own account.")
        self._ensure_not_last_admin(target_user)
        self._delete_user_with_dependencies(target_user)

    def _build_identity_changes(
        self,
        target_user: User,
        username: str | None = None,
        email: str | None = None,
    ) -> dict[str, object]:
        changes: dict[str, object] = {}

        if username is not None:
            normalized_username = username.strip()
            if not normalized_username:
                raise UserValidationError("Username cannot be empty.")
            existing_user = self.user_repo.get_by_username(normalized_username)
            if existing_user and existing_user.id != target_user.id:
                raise UserConflictError("Username already exists.")
            changes["username"] = normalized_username

        if email is not None:
            normalized_email = str(email).strip().lower()
            if not normalized_email:
                raise UserValidationError("Email cannot be empty.")
            existing_user = self.user_repo.get_by_email(normalized_email)
            if existing_user and existing_user.id != target_user.id:
                raise UserConflictError("Email already exists.")
            changes["email"] = normalized_email

        return changes

    def _ensure_not_last_admin(self, user: User) -> None:
        if user.role != "admin":
            return
        if self.user_repo.count_by_role("admin") <= 1:
            raise UserConflictError("StormScope must keep at least one admin account.")

    def _delete_user_with_dependencies(self, user: User) -> None:
        if self.saved_location_repo:
            self.saved_location_repo.delete_for_user(user.id)
        if self.disaster_repo:
            self.disaster_repo.clear_created_by(user.id)
        self.user_repo.delete_user(user)

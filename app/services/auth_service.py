from app.repositories.user import UserRepository
from app.schemas.user import RegularUserCreate
from app.utilities.security import create_access_token, encrypt_password, verify_password
from typing import Optional

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(plaintext_password=password, encrypted_password=user.password_hash):
            return None
        access_token = create_access_token(data={"sub": f"{user.id}", "role": user.role})
        return access_token

    def register_user(self, username: str, email: str, password: str):
        if self.user_repo.get_by_username(username):
            raise ValueError("Username already exists")
        if self.user_repo.get_by_email(email):
            raise ValueError("Email already exists")
        new_user = RegularUserCreate(
            username=username, 
            email=email, 
            password=password,
        )
        return self.user_repo.create(new_user, password_hash=encrypt_password(password))

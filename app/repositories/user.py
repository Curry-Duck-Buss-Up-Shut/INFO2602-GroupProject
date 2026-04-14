import logging
from typing import Optional, Tuple

from sqlmodel import Session, func, select

from app.models.user import User
from app.schemas.user import UserCreate
from app.utilities.pagination import Pagination

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_data: UserCreate, password_hash: str) -> Optional[User]:
        try:
            user_db = User(
                username=user_data.username,
                email=user_data.email,
                password_hash=password_hash,
                role=user_data.role,
            )
            self.db.add(user_db)
            self.db.commit()
            self.db.refresh(user_db)
            return user_db
        except Exception as e:
            logger.error(f"An error occurred while saving user: {e}")
            self.db.rollback()
            raise

    def search_users(self, query: str, page:int=1, limit:int=10) -> Tuple[list[User], Pagination]:
        offset = (page - 1) * limit
        db_qry = select(User)
        if query:
            db_qry = db_qry.where(
                User.username.ilike(f"%{query}%") | User.email.ilike(f"%{query}%")
            )
        count_qry = select(func.count()).select_from(db_qry.subquery())
        count_todos = self.db.exec(count_qry).one()

        users = self.db.exec(db_qry.offset(offset).limit(limit)).all()
        pagination = Pagination(total_count=count_todos, current_page=page, limit=limit)

        return users, pagination

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.exec(select(User).where(User.username == username)).one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.exec(select(User).where(User.email == email)).one_or_none()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_all_users(self) -> list[User]:
        statement = select(User).order_by(User.created_at.desc())
        return list(self.db.exec(statement).all())

    def count_by_role(self, role: str) -> int:
        statement = select(func.count()).where(User.role == role)
        return int(self.db.exec(statement).one())

    def update_user(self, user: User, changes: dict[str, object]) -> User:
        for field, value in changes.items():
            setattr(user, field, value)

        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            logger.error(f"An error occurred while updating user: {e}")
            self.db.rollback()
            raise

    def delete_user(self, user: User) -> None:
        try:
            self.db.delete(user)
            self.db.commit()
        except Exception as e:
            logger.error(f"An error occurred while deleting user: {e}")
            self.db.rollback()
            raise

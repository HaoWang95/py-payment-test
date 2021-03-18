from sqlalchemy.orm import Session

from Models import User, PaymentRecord, PaymentAccount
from Schemas import CreateUserRequest


def get_user(db: Session, user_id: int):
    return db.query(User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: CreateUserRequest):
    fake_hashed_password = user.password
    db_user = User(
        first = user.first, last = user.last, 
        email = user.email, password = fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


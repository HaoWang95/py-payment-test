from sqlalchemy.orm import Session

from .Models import Users as User, UserModel

# Find user by id
def get_user(db: Session, user_id: int):
    return db.query(UserModel).filter(UserModel.id == user_id).first()

# Find user by email
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(models.User.email == email).first()

# Find all users
def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()



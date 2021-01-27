from sqlalchemy.orm import Session
from dbcomp import access, models

from . import models, schemas

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.pblacore_uid == user_id).first()
    # return db.query(*[c for c in models.User.__table__.c if c.name != 'driveapi_token']).filter(models.User.pblacore_uid == user_id).all()

def create_user(db: Session, user_id: int, creds: str, name: str, mail: str):
    db_user = models.User(pblacore_uid=user_id, driveapi_token=creds, driveapi_name=name, driveapi_email=mail)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_status(db: Session, user_id: int, is_active: bool):
    db_user = models.User(pblacore_uid=user_id, is_active=is_active)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)    
    return db_user.is_active


# def get_user_by_email(db: Session, email: str):
#     return db.query(models.User).filter(models.User.email == email).first()


# def get_users(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.User).offset(skip).limit(limit).all()

# def get_items(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.Item).offset(skip).limit(limit).all()

# def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
#     db_item = models.Item(**item.dict(), owner_id=user_id)
#     db.add(db_item)
#     db.commit()
#     db.refresh(db_item)
#     return db_item
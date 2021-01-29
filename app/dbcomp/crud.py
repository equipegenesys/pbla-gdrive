from sqlalchemy.orm import Session
from dbcomp import access, models
from . import models, schemas


def get_user(db: Session, user: schemas.UserBase):
	return db.query(models.User).filter(models.User.pblacore_uid == user.pblacore_uid).first()


def create_user(db: Session, user_to_create: schemas.UserCreate):
	if not db.query(models.User).filter(models.User.driveapi_email == user_to_create.driveapi_email).first():

		db_user = models.User(pblacore_uid=user_to_create.pblacore_uid,
							  driveapi_token=user_to_create.pblacore_token,
							  driveapi_name=user_to_create.driveapi_name,
							  driveapi_email=user_to_create.driveapi_email)
		db.add(db_user)
		db.commit()
		db.refresh(db_user)
		return f"A conta do Google Drive de {db_user.driveapi_email} foi integrada ao usuário do PBL Analytics com ID {db_user.pblacore_uid}."
	return "Já existe um usuário cadastrado com esse e-mail"


def get_turma(db: Session, turma: schemas.TurmaBase):
	return db.query(models.Turma).filter(models.Turma.pblacore_sku_turma == turma).first()


def create_turma(db: Session, turma_to_create: schemas.TurmaCreate):
	db_turma = models.Turma(pblacore_sku_turma=turma_to_create.pblacore_sku_turma,
							pblacore_disci_turma=turma_to_create.pblacore_disci_turma,
							pblacore_ano_turma=turma_to_create.pblacore_ano_turma,
							pblacore_semestre_turma=turma_to_create.pblacore_semestre_turma)
	db.add(db_turma)
	db.commit()

	if turma_to_create.users != None:
		user_query = schemas.UserBase
		for user in turma_to_create.users:
			user_query.pblacore_uid = user
			db_user = get_user(db=db, user=user_query)
			if db_user:
				db_turma.users.append(db_user)
				db.commit()

	db.refresh(db_turma)
	return db_turma


def add_user_turma(db: Session, turma: schemas.TurmaAddUser):
	selected_turma = db.query(models.Turma).get(turma.pblacore_sku_turma)
	if turma.users is not None:
		user_query = schemas.UserBase
		for user in turma.users:
			user_query.pblacore_uid = user
			db_user = get_user(db=db, user=user_query)
			if db_user is not None:
				selected_turma.users.append(db_user)
				db.commit()
		estudantes = {'estudantes': []}	
		for user in selected_turma.users:
			userDict = user.basicData()
			estudantes['estudantes'].append(userDict)
		return {'turma': estudantes}
	return "Não a há usuários no corpo do HTTP POST"

# def create_user_item(db: Session, turma: schemas.TurmaAddUser, user_id: int):
# 	db_item = models.Item(**item.dict(), owner_id=user_id)
# 	db.add(db_item)
# 	db.commit()
# 	db.refresh(db_item)
# 	return db_item

# def update_user_status(db: Session, user_id: int, is_active: bool):
#     db_user = models.User(pblacore_uid=user_id, is_active=is_active)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user.is_active


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

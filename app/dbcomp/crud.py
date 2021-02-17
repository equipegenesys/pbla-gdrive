from sqlalchemy.orm import Session
from dbcomp import access, models
from . import models, schemas, access
import pickle


def get_user(db: Session, user: schemas.UserBase):
    error = {}
    try:
        db_user = db.query(models.User).filter(
            models.User.pblacore_uid == user.pblacore_uid).first()
        return db_user
    except pickle.UnpicklingError as e:
        error = {"user_id": user.pblacore_uid, "cadastrado": True,
                 "integrado": False, "info¨": "Token corrompido"}
        return error


def create_user_fromgdrive(db: Session, user_to_create: schemas.UserCreate):
    if not db.query(models.User).filter(models.User.driveapi_email == user_to_create.driveapi_email).first():

        db_user = models.User(pblacore_uid=user_to_create.pblacore_uid,
                              driveapi_token=user_to_create.pblacore_token,
                              driveapi_name=user_to_create.driveapi_name,
                              driveapi_email=user_to_create.driveapi_email)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"msg": f"A conta do Google Drive de {db_user.driveapi_email} foi integrada ao usuário do PBL Analytics com ID {db_user.pblacore_uid}."}
    return {"msg": "Já existe um usuário cadastrado com esse e-mail"}


def create_user_fromcore(db: Session, user_to_create: schemas.UserBase):
    if not db.query(models.User).filter(models.User.driveapi_email == user_to_create.pblacore_email).first():

        db_user = models.User(pblacore_uid=user_to_create.pblacore_uid,
                              pblacore_email=user_to_create.pblacore_email,
                              pblacore_nome=user_to_create.pblacore_nome)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"msg": f"A conta do PBL Core com ID {db_user.pblacore_uid} foi adicionada ao gateway de integração."}
    return {"msg": "Esse usuário já está cadastrado"}


def update_token(db: Session, user_to_update: schemas.UserCreate):
    # em caso de token corrompido, é preciso gravar um NULL no field, senão o query em seguida falha
    db_connection = access.engine_app_db.connect()
    db_connection.execute(
        f'UPDATE users SET driveapi_token = NULL WHERE pblacore_uid = {user_to_update.pblacore_uid};')
    db_connection.close()
    db_user = db.query(models.User).filter(
        models.User.pblacore_uid == user_to_update.pblacore_uid).first()
    db_user.driveapi_token = user_to_update.pblacore_token
    db_user.driveapi_email = user_to_update.driveapi_email
    db_user.driveapi_name = user_to_update.driveapi_name
    db.commit()
    db.refresh(db_user)
    return {"msg": f"A conta do Google Drive de {db_user.driveapi_email} teve seu token atualizado no PBL Analytics com ID {db_user.pblacore_uid}."}


def update_core_user_data(db: Session, user_to_update: schemas.UserBase):
    if db.query(models.User).filter(models.User.pblacore_uid == user_to_update.pblacore_uid).first():
        db_user = db.query(models.User).filter(
            models.User.pblacore_uid == user_to_update.pblacore_uid).first()
        db_user.pblacore_email = user_to_update.pblacore_email
        db_user.pblacore_nome = user_to_update.pblacore_nome
        db.commit()
        db.refresh(db_user)
        return {"msg": f"O usuário do PBL Analytics com ID {db_user.pblacore_uid} teve dados de e-mail e nome agregados."}
    return {"msg": "Não existe um usuário cadastrado com esse pblacore_uid"}


def get_turma(db: Session, turma: schemas.TurmaBase):
    return db.query(models.Turma).filter(models.Turma.pblacore_sku_turma == turma).first()


def create_turma(db: Session, turma_to_create: schemas.TurmaAdd):
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


def create_turma_simples(db: Session, turma_to_create: schemas.TurmaBase):
    db_turma = models.Turma(pblacore_sku_turma=turma_to_create.pblacore_sku_turma,
                            pblacore_disci_turma=turma_to_create.pblacore_disci_turma,
                            pblacore_ano_turma=turma_to_create.pblacore_ano_turma,
                            pblacore_semestre_turma=turma_to_create.pblacore_semestre_turma)
    db.add(db_turma)
    db.commit()


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
    return {"msg": "Não a há usuários no corpo do HTTP POST"}


def add_user_turma_simples(db: Session, turma: str, user: str):
    selected_turma = db.query(models.Turma).get(turma.pblacore_sku_turma)
    db_user = get_user(db=db, user=user)
    selected_turma.users.append(db_user)
    db.commit()


def check_user_in_turma(db: Session, turma: str, user: str):
    rquery = db.query(models.user_turma_table).join(models.Turma).join(models.User).filter(
        models.Turma.pblacore_sku_turma == turma, models.User.pblacore_uid == user).first()
    return rquery


def get_files(db: Session, file: schemas.FileBase):
    return db.query(models.File).filter(models.File.driveapi_fileid == file.driveapi_fileid).first()


def create_file(db: Session, file: schemas.TurmaAddUser, user: schemas.UserBase, turma: schemas.TurmaBase):
    db_file = models.File(driveapi_fileid=file.driveapi_fileid,
                          is_active=file.is_active)
    db_file.users.append(user)
    db_file.turmas.append(turma)

    db.add(db_file)
    db.commit()
    created_db_file = get_files(db=db, file=db_file)
    models.tableCreator(tablename=created_db_file.local_fileid)


def update_file(db: Session, file_to_update: str, user: int, turma: str):
    db_user = db.query(models.User).filter(
        models.User.pblacore_uid == user).first()
    db_turma = db.query(models.Turma).filter(
        models.Turma.pblacore_sku_turma == turma).first()
    if db.query(models.File).filter(models.File.driveapi_fileid == file_to_update).first():
        db_file = db.query(models.File).filter(
            models.File.driveapi_fileid == file_to_update).first()
        db_file.is_active = True
        db_file.users.append(db_user)
        db_file.turmas.append(db_turma)
        db.commit()
        db.refresh(db_file)


def create_file_record(db: Session, file_record: schemas.FileRecords):
    db_file_record = models.FileRecords(name=file_record)
    db.add(db_file_record)
    db.commit()


def get_file_record(db: Session, file_record: str):
    return db.query(models.FileRecords).filter(models.FileRecords.__tablename__ == file_record).first()

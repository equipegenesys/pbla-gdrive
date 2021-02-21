from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import google.oauth2.credentials
import googleapiclient.discovery
import os
import json
from sqlalchemy.orm import Session
from dbcomp import crud, access, schemas
from typing import (
	Deque, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple, Union
)
from driveapi import files, auth

CLIENT_SECRETS_FILE = '/app/driveapi/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
		  'https://www.googleapis.com/auth/drive.activity.readonly']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

router = APIRouter()


@router.post('/api/integ/gdrive/add/turma')
def add_user_turma(turma: schemas.TurmaAdd, db: Session = Depends(access.get_app_db)):
	# se a turma tem estudantes...
	if turma.users != None:
		users_created = []
		users_already = []
		users_added = []
		# se a turma já existe na db...
		if crud.get_turma(db=db, turma=turma.pblacore_sku_turma) != None:
			# para cada usuário listado na turma...
			for user in turma.users:
				# se usuário não existe...
				if crud.get_user(db=db, user=user) == None:
					# crie usuário
					crud.create_user_fromcore(db=db, user_to_create=user)
					# adicione usuário à turma que já existe
					crud.add_user_turma_simples(db=db, turma=turma, user=user)
					# adicione nome do user à lista de usuários criados e adicionados à turma
					users_created.append(user.pblacore_nome)
				# se usuário existe...
				else:
					crud.update_core_user_data(db=db, user_to_update=user)
					# se usuário já estiver nessa turma
					if crud.check_user_in_turma(db=db, turma=turma.pblacore_sku_turma, user=user.pblacore_uid):
						# adicione nome do user à lista de usuários que já existiam e estavam na turma
						users_already.append(user.pblacore_nome)
					# se usuário ainda não estiver na turma
					else:
						# adicione usuário à turma que já existe
						crud.add_user_turma_simples(db=db, turma=turma, user=user)
						# adicione nome do user à lista de usuários que já existiam e foram adicionados à turma
						users_added.append(user.pblacore_nome)
					# verifique se usuário tem uma integração
					# print("                user.pblacore_uid era:", user.pblacore_uid)
					integ_status = auth.check_integ_status(db=db, user_id=user.pblacore_uid)
					if integ_status['integrado'] == True:
						# listar arquivos (o que já atualiza a tabela de arquivos e cria tabelas individuais para cada um)
						print("é 1")				
						files.list_files(db=db, user_id=user.pblacore_uid)
			return f"A turma {turma.pblacore_sku_turma} já existia. Os usuários {users_created} foram criados e adicionados à turma. Os usuários {users_added} já existiam e foram adicionados. Os usuários {users_already} já estavam na turma."
		# se turma não existe na db
		else:
			# crie turma
			crud.create_turma_simples(db=db, turma_to_create=turma)
			# para cada usuário listado na turma...
			for user in turma.users:
				#se usuário não existe...
				if crud.get_user(db=db, user=user) == None:
					# crie usuário
					crud.create_user_fromcore(db=db, user_to_create=user)
					# adicione usuário à turma que já existe
					crud.add_user_turma_simples(db=db, turma=turma, user=user)
					# adicione nome do user à lista de usuários criados e adicionados à turma
					users_created.append(user.pblacore_nome)
				# se usuário existe...
				else:
					crud.update_core_user_data(db=db, user_to_update=user)
					# adicione usuário à turma
					crud.add_user_turma_simples(db=db, turma=turma, user=user)
					# adicione nome do user à lista de usuários que já existiam e foram adicionados à turma
					users_added.append(user.pblacore_nome)
									# verifique se usuário tem uma integração
					integ_status = auth.check_integ_status(db=db, user_id=user.pblacore_uid)
					if integ_status['integrado'] == True:
						# listar arquivos (o que já atualiza a tabela de arquivos e cria tabelas individuais para cada um)
						print("é 2")
						files.list_files(db=db, user_id=user.pblacore_uid)
			return f"A turma {turma.pblacore_sku_turma} foi criada. Os usuários {users_created} foram criados e adicionados à turma. Os usuários {users_added} já existiam e foram adicionados."
	return {"msg": "Http POST veio sem uma lista de usuários (estudantes). Nada foi feito."}
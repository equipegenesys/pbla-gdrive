import requests

def get_turmas_from_core(user_id: int):
	url = "http://172.22.0.3:8000/api/core/turmas/user/"
	response = requests.get(f'{url}{user_id}/?format=json')
	response = response.json()
	return  response['turma-equipe']

def create_integration_record(integration_type: str, id: int, is_active: bool):
	url = f"http://172.22.0.3:8000/api/core/integ/{integration_type}/"
	payload = {integration_type: id, 'integracao': 1, 'is_active': is_active}
	return requests.post(url, json = payload)

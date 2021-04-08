import requests

def get_turmas_from_core(user_id: int):
	url = "http://172.22.0.8:8000/api/core/turmas/user/"
	response = requests.get(f'{url}{user_id}/?format=json')
	response = response.json()
	return  response['turmas']
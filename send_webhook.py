import requests
import json


def send_info_n8n(dicionario_python, headers):

    #link = 'http://localhost:5678/webhook/aaef0ef4-c33c-4392-9d2e-81cb399025d7'

    # Link do ambiente N8N (local): 
    link = 'http://localhost:5678/webhook-test/aaef0ef4-c33c-4392-9d2e-81cb399025d7'
    # Link para teste online:
    #link = 'https://webhook.site/ea229e59-ae9b-46fe-9994-5192610a2386'

    # Convertendo dicionario Python em um Json
    dicionario_ = json.dumps(dicionario_python, default=str)
    
    requests.post(link, data=dicionario_, headers=headers)

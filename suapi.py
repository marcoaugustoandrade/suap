#!/bin/python3
import requests, gspread
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv
load_dotenv()

username = os.getenv("SUAP_USERNAME")
pwd = os.getenv("SUAP_PASSWORD")
spreadsheet_url = os.getenv("SPREADSHEET_URL")

LBL_DATE = "data"
LBL_QTDD_PRATICA = "quantidade aulas práticas"
LBL_QTDD_TEORICA = "quantidade aulas teóricas"
LBL_CONTEUDO = "conteudo"
LBL_TIPO_FREQ = "tipo de frequencia"
LBL_UPDATED = "updated"
LBL_INICIO = "inicio"

HOUR = { "07:10":312,
         "08:00":313,
         "08:50":314,
         "09:55":315,
         "10:45":316,
         "13:10":307,
         "14:00":308,
         "14:50":309,
         "15:55":310,
         "16:45":311,
         "17:20":346,
         "18:10":302,
         "19:00":303,
         "19:50":304,
         "20:55":305,
         "21:45":306,
}


def get_tipo_freq_code(tipo_frequencia):
    if tipo_frequencia == 'Presencial':
        return 0
    elif tipo_frequencia == 'Não Presencial':
        return 1


# retorna o código do horário de início da aula
def get_hour_code(hour):
    return HOUR[hour]


#usado para retornar somente linhas que as datas foram lançadas e que ainda não foram
#lançadas no sistema (updated:FALSE)
def filter_data(line):
    #0: data
    return line[LBL_DATE] and not line[LBL_UPDATED]


def map_data(data):
    new_list = []

    for line in data[1:]:
        d = dict(zip (data[0], line))
        if d[LBL_UPDATED] == 'TRUE':
            d[LBL_UPDATED] = True
        else:
            d[LBL_UPDATED] = False
        new_list.append(d)
    new_list = list(filter(filter_data, new_list))
    return new_list


def get_csrftoken(session):
    if 'csrftoken' in session.cookies:
        return session.cookies['csrftoken']
    else:
        return session.cookies['csrf']


# tenta fazer login e retorna um objeto do tipo Session (requests)
def login():
    global username, pwd
    if username is None:
        username = input("Digite o nome de usuário do SUAP:")

    if pwd is None:
        from getpass import getpass
        pwd = getpass()

    payload = {'username' : username, 'password': pwd}
    csrftoken = None
    s = requests.Session()
    s.get("https://suap.ifro.edu.br/accounts/login/")

    csrftoken = get_csrftoken(s)
    payload['csrfmiddlewaretoken'] = csrftoken
    r = s.post("https://suap.ifro.edu.br/accounts/login/", data=payload)

    if r.status_code != 200:
        print("erro ao fazer login")
        print(r.status_code)
        return None
    else:
       return s


def busca_diarios(session):
    r = session.get("https://suap.ifro.edu.br/edu/meus_diarios/")
    soup = BeautifulSoup(r.text, 'html.parser')
    tables = []
    for index, table in enumerate(soup.find_all('table', {"class":"marginBottom20"})):
        caption = table.caption.text
        url = table.tbody.find_all('td')[2].ul.find_all('li')[0].find_all('a')[0]['href']
        d = {'caption':table.caption.text, 'url':url, 'index':index}
        tables.append(d)
    return tables

def parse_id_diario(diario):
    global url
    url = diario['url']
    id_diario = url.split("meu_diario/")[1].split("/")[0]
    return id_diario


# consulta o usuário sobre qual diário quer atualizar e retorna o id do dirio
def consulta_qual_diario(diarios):
    print("--- Escolha o diário que você quer atualizar ---")
    for diario in diarios:
        print(f"{diario['index']}: {diario['caption']}")
    escolha = int(input("Escolha: "))
    id_diario = parse_id_diario(diarios[escolha])
    return id_diario


def init_gspread():
    global spreadsheet_url
    gc = gspread.service_account(filename='./service_account.json')
    if spreadsheet_url is None:
        spreadsheet_url = input("Digite a URL da planilha")

    sh = gc.open_by_url(spreadsheet_url)
    return sh


#pega a primeira planilha e retorna os dados mapeados em um dict
def select_worksheet(sheet, index=0):
    worksheet = sheet.get_worksheet(index)
    data = worksheet.get_all_values()
    data = map_data(data)
    return data

'''
middlewaretoken: e2EEvYwGZagYBLRBshsYKgRKvJWUeOBSOW31ENMksp8dru71ulp6gdfB8dp5UcdK
professor_diario: 704
tipo_frequencia: 0
quantidade: 2
quantidade_aula_teorica: 1
quantidade_aula_pratica: 1
etapa: 1
data: 07/10/2020
horario_inicio: 305
conteudo: Preenchimento posterior.
q: 
aula_form
'''


def map_data_to_payload(data, professor_diario, csrftoken = None):
    payload = {}
    if csrftoken:
        payload['csrfmiddlewaretoken'] = csrftoken
    payload['professor_diario'] = professor_diario
    payload['tipo_frequencia'] = get_tipo_freq_code(data[LBL_TIPO_FREQ])
    payload['quantidade_aula_teorica'] = data[LBL_QTDD_TEORICA]
    payload['quantidade_aula_pratica'] = data[LBL_QTDD_PRATICA]
    payload['quantidade'] = str(int(data[LBL_QTDD_TEORICA]) + int(data[LBL_QTDD_PRATICA]))
    payload['etapa'] = 1
    payload['data'] = data[LBL_DATE]
    payload['horario_inicio'] = get_hour_code(data[LBL_INICIO])
    payload['conteudo'] = data[LBL_CONTEUDO]
    payload['q']=''
    payload['aula_form']='Aguarde...'
    return payload

def adiciona_aula(id_diario, data, session):
    d = {'Host': 'suap.ifro.edu.br',
         'Connection': 'keep-alive',
         'Content-Length': '277',
         'Cache-Control': 'max-age=0',
         'Upgrade-Insecure-Requests': '1',
         'Origin': 'https://suap.ifro.edu.br',
         'Content-Type': 'application/x-www-form-urlencoded',
         'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
         'Sec-Fetch-Site': 'same-origin',
         'Sec-Fetch-Mode': 'navigate',
         'Sec-Fetch-User': '?1',
         'Sec-Fetch-Dest': 'document',
         'Referer': f'https://suap.ifro.edu.br/edu/adicionar_aula_diario/{id_diario}/1/?_popup=1',
         'Accept-Encoding': 'gzip, deflate, br',
         'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',}
    url = f"https://suap.ifro.edu.br/edu/adicionar_aula_diario/{id_diario}/1/"
    r = session.get(url)
    csrftoken = get_csrftoken(session)
    #print(r.text)
    soup = BeautifulSoup(r.text, 'html.parser')
    professor_diario = soup.find("input", {'id':'id_professor_diario'})['value']
    payload = map_data_to_payload(data, professor_diario, csrftoken)
    print(payload)
    #print("Publicando aula {}".format(payload))
    #print(session.cookies.get_dict())
    #r = session.post(url, data=payload, headers=session.headers.update({'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'}))
    r = session.post(url, data=payload, allow_redirects=True) 
    print(r.request.headers)
    print(r.status_code)
    print(r.request)

def main():
    session = login()
    print(session)
    diarios = busca_diarios(session)
    id_diario = consulta_qual_diario(diarios)
    sheet = init_gspread()
    data = select_worksheet(sheet)
    for line in data:
        adiciona_aula(id_diario, line, session)

if __name__ == "__main__":
    main()


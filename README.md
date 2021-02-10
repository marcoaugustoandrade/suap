# suapi

## Instalação
pip install -r requirements.txt

## Configuração
Faça uma cópia do arquivo `.env.example`:
cp .env.example .env

Edite o arquivo `.env` com as suas credenciais de acesso ao SUAP.

Crie um novo projeto em https://console.developers.google.com/cloud-resource-manager

Na caixa de busca, onde está escrito "Search for APIs and Services", procure por "Google Drive API" e habilite.

Na caixa de busca, onde está escrito "Search for APIs and Services", procure por "Google Sheets API" e habilite.

No menu vá em "APIs & Services" > "Credentials", clique no botão "+ CREATE CREDENTIALS" e selecione "Service account", defina "Service account name" e clique no botão "Done".

Clique no Service account criado, clique no botão "Add Key" > "Create new Key" e selecione o formato JSON para criar uma nova chave de acesso.

Baixe o arquivo `service_account.json` e coloque na raiz deste projeto.

Abra e faça uma cópia da planilha https://docs.google.com/spreadsheets/d/1VI6PHLmcCgK0SGXF4qxdm5BXoAg6Sg-tvFlF_YgH48U/edit#gid=356176471

Compartilhe a sua planilha com o email indicado dentro do arquivo `service_account.json`.

Mais instruções podem ser encontradas em https://gspread.readthedocs.io/en/latest/oauth2.html


## Executando o projeto
python3 suapi.py

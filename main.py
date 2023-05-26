#import os
import ssl
import gspread
import time

from slack_sdk import WebClient
from google.oauth2 import service_account

# Disable SSL certificate verification
ssl._create_default_https_context = ssl._create_unverified_context

credentials = service_account.Credentials.from_service_account_file(
  'credentials.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])

client = gspread.authorize(credentials)
spreadsheet = client.open_by_key(
  '1sCd56Fl5Bx6jpSD9n41IJKsiQYo_MXadYMFQAnftgOw')
sheet = spreadsheet.sheet1

# Token de autenticación de la API de Slack
# SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
SLACK_TOKEN = 'xoxb-5310427832679-5322047644949-KgXKmcPvXQcbQMl7Ep8bhi4d'


def read_messages(channel_id):
  client = WebClient(token=SLACK_TOKEN)
  response = client.conversations_history(channel=channel_id)
  if response["ok"]:
    values_list = sheet.col_values(1)
    print(values_list)
    for message in response["messages"]:
      #print(message["text"])
      if not [value for value in values_list if [value] == [message["text"]]]:
        sheet.append_row([message["text"]])

  else:
    print("No se pudo obtener el historial de mensajes.")


# ID del canal de Slack que deseas leer
channel_id = "C059ME2HV9A"
while True:
  read_messages(channel_id)
  time.sleep(5)

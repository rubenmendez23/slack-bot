import ssl
import time
from flask import Flask, jsonify
from flask_socketio import SocketIO
from slack_sdk import WebClient
from slack_sdk.rtm import RTMClient
from google.oauth2 import service_account
import gspread
import threading

from dotenv import load_dotenv
import os

# Errores en app.log
import logging
from logging.handlers import RotatingFileHandler

# Cargar variables de entorno desde el archivo .env
load_dotenv()  # pip install python-dotenv

# Configuración de Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('APP_KEY')  # Reemplaza con tu clave secreta real
socketio = SocketIO(app)

# Configuración del registro de mensajes
log_file = "app.log"
logging.basicConfig(filename=log_file, level=logging.DEBUG)

# Configuración de Slack
SLACK_TOKEN =os.environ.get('TOKEN_SLACK')  # Reemplaza con tu token de Slack

# Configuración de Google Sheets
credentials = service_account.Credentials.from_service_account_file('credentials.json', scopes=[os.environ.get('SCOPES')])
client = gspread.authorize(credentials)
spreadsheet = client.open_by_key(os.environ.get('SPREADSHEET_KEY'))
sheet = spreadsheet.sheet1

# Deshabilitar la verificación del certificado SSL
ssl._create_default_https_context = ssl._create_unverified_context

# Lista global para almacenar los mensajes
messages = []

# Función para leer mensajes de Slack y actualizar la lista global
def read_messages(channel_id):
    while True:
        slack_client = WebClient(token=SLACK_TOKEN)
        success = False
        try:
            response = slack_client.conversations_history(channel=channel_id)
            success = True
        except Exception as e:
             logging.debug("Error al obtener el historial de mensajes de Slack:", str(e))

        if success:
            if response["ok"]:
                new_messages = [message["text"] for message in response["messages"]]
                messages.extend(new_messages)  # Agregar los nuevos mensajes a la lista global
                update_spreadsheet(new_messages)  # Actualizar el archivo de Google Sheets
            else:
                 logging.debug("No se pudo obtener el historial de mensajes de Slack.")
        time.sleep(5)  # Esperar 5 segundos antes de realizar la siguiente lectura

# Función para actualizar el archivo de Google Sheets con los mensajes
def update_spreadsheet(new_messages):
    values_list = sheet.col_values(1)  # Obtener los valores de la primera columna
    for message in new_messages:
        if message not in values_list:
            sheet.append_row([message])  # Agregar el mensaje al archivo
            messages.append(message)  # Agregar el mensaje a la lista global

# Controlador de ruta para la página principal
# http://127.0.0.1:5000/
@app.route('/')
def index():
    return jsonify({"message": messages})

# Controlador de eventos para el evento de conexión WebSocket
@socketio.on('connect')
def handle_connect():
     logging.debug('Se ha establecido una conexión WebSocket')

# Controlador de eventos para el evento de desconexión WebSocket
@socketio.on('disconnect')
def handle_disconnect():
     logging.debug('Se ha desconectado una conexión WebSocket')


# RTM => Comunicacion en tiempo real
@RTMClient.run_on(event="message")
def handle_rtm_message(**payload):
    data = payload["data"]
    if "text" in data:
        message = data["text"]
        logging.debug("Mensaje recibido:")
        logging.debug(message) # Json con info de la conexion y con el json de todos los mensajes del canal
        messages.append(message)  # Agregar el mensaje a la lista global
        read_messages(channel_id)

def start_rtm_client():
    rtm_client = RTMClient(token=SLACK_TOKEN)
    rtm_client.start()

if __name__ == '__main__':
    channel_id = os.environ.get('CANAL_SLACK')  # ID del canal de Slack que deseas leer
    logging.debug("_"*100)
    threading.Thread(target=read_messages, args=(channel_id,)).start()  # Inicia la lectura de mensajes en otro hilo
    socketio.run(app, debug=True,port=5000,load_dotenv=True)

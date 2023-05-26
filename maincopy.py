import ssl
import time
from flask import Flask, jsonify
from flask_socketio import SocketIO
from slack_sdk import WebClient
from slack_sdk.rtm import RTMClient
from google.oauth2 import service_account
import gspread
import threading

# Configuración de Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'boteros123456789'  # Reemplaza con tu clave secreta real
socketio = SocketIO(app)

# Configuración de Slack
SLACK_TOKEN = ''  # Reemplaza con tu token de Slack

# Configuración de Google Sheets
credentials = service_account.Credentials.from_service_account_file('credentials.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
client = gspread.authorize(credentials)
spreadsheet = client.open_by_key('1sCd56Fl5Bx6jpSD9n41IJKsiQYo_MXadYMFQAnftgOw')
sheet = spreadsheet.sheet1

# Deshabilitar la verificación del certificado SSL
ssl._create_default_https_context = ssl._create_unverified_context

# Lista global para almacenar los mensajes
messages = []
# new_messages = []



# Función para leer mensajes de Slack y actualizar la lista global
def read_messages(channel_id):
    # global messages
    while True:
        slack_client = WebClient(token=SLACK_TOKEN)
        success = False
        try:
            response = slack_client.conversations_history(channel=channel_id)
            success = True
        except Exception as e:
            print("Error al obtener el historial de mensajes de Slack:", str(e))

        if success:
            if response["ok"]:
                new_messages = [message["text"] for message in response["messages"]]
                messages.extend(new_messages)  # Agregar los nuevos mensajes a la lista global
                update_spreadsheet(new_messages)
            else:
                print("No se pudo obtener el historial de mensajes de Slack.")
        time.sleep(5)  # Esperar 5 segundos antes de realizar la siguiente lectura

# Función para actualizar el archivo de Google Sheets con los mensajes
def update_spreadsheet(new_messages):
    values_list = sheet.col_values(1)  # Obtener los valores de la primera columna
    for message in new_messages:
        if message not in values_list:
          sheet.append_row([message])  # Agregar el mensaje al archivo
          messages.append(message)  # Agregar el mensaje a la lista global

# # Controlador de ruta para la página principal
@app.route('/')
def index():
  return jsonify({"message": messages})

# Controlador de eventos para el evento de conexión WebSocket
@socketio.on('connect')
def handle_connect():
    print('Se ha establecido una conexión WebSocket')

# Controlador de eventos para el evento de desconexión WebSocket
@socketio.on('disconnect')
def handle_disconnect():
    print('Se ha desconectado una conexión WebSocket')

@RTMClient.run_on(event="message")
def handle_rtm_message(**payload):
    # Aquí puedes manejar el mensaje recibido
    data = payload["data"]
    if "text" in data:
        message = data["text"]
        print("Mensaje recibido:", message)
        read_messages(channel_id)

def start_rtm_client():
    rtm_client = RTMClient(token=SLACK_TOKEN)
    rtm_client.start()

if __name__ == '__main__':
    channel_id = "C059JUWT2D8"  # ID del canal de Slack que deseas leer
    # threading.Thread(target=read_messages, args=(channel_id,)).start()  # Inicia la lectura de mensajes en otro hilo
    socketio.run(app, debug=False)

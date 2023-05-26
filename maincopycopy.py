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
SLACK_TOKEN = 'xoxb-5310427832679-5322047644949-tnHDiuF2kpjzNSgpURbKUPA3'  # Reemplaza con tu token de Slack

# Configuración de Google Sheets
credentials = service_account.Credentials.from_service_account_file('credentials.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
client = gspread.authorize(credentials)
spreadsheet = client.open_by_key('1sCd56Fl5Bx6jpSD9n41IJKsiQYo_MXadYMFQAnftgOw')
sheet = spreadsheet.sheet1

# Deshabilitar la verificación del certificado SSL
ssl._create_default_https_context = ssl._create_unverified_context

# Controlador de ruta para la página principal
@app.route('/inicio')
def index():
    while True:
        messages = read_messages(channel_id)
        if isinstance(messages, list):
            for message in messages:
            # Verificar si el mensaje ya existe en el archivo
                values_list = sheet.col_values(1)  # Obtener los valores de la primera columna
                if message not in values_list:
                    sheet.append_row([message])  # Agregar el mensaje al archivo
            return jsonify({"message": messages})
        else:
            return("\nSin mensajes")

# Función para leer mensajes de Slack y devolver el texto de respuesta
def read_messages(channel_id):
    slack_client = WebClient(token=SLACK_TOKEN)
    succses = False
    # try:
    response = slack_client.conversations_history(channel=channel_id)
    succses = True
    # except Exception as e:
        # print("Error al obtener el historial de mensajes de Slack:", str(e))


    if(succses):
        if response["ok"]:
            messages = [message["text"] for message in response["messages"]]
            return messages
        else:
            return "No se pudo obtener el historial de mensajes de Slack."
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

def start_rtm_client():
    rtm_client = RTMClient(token=SLACK_TOKEN)
    rtm_client.start()


if __name__ == '__main__':
    channel_id = "C059JUWT2D8"  # ID del canal de Slack que deseas leer
    threading.Thread(target=start_rtm_client).start()  # Inicia el cliente RTM en un hilo separado
    socketio.run(app, debug=False)

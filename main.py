from flask import Flask
from flask_socketio import SocketIO, emit
from flask import Flask, request,jsonify
from flask_cors import CORS
import requests
import json
import os
import asyncio
import http
import signal
import json

app = Flask(__name__)
CORS(app,resources={r"/*":{"origins":"*"}})
socketio = SocketIO(app,cors_allowed_origins="*")


class Conversations:
   def update_botdata(self, botdata, new_integration_id):
     botdata['integration_id'] = new_integration_id
     return botdata
   
   def get_bot_integrations(self, botdata):
   
     url = f"https://api.botpress.cloud/v1/admin/bots/{botdata['botid']}"
     headers = {
         "Accept": "application/json",
         "Authorization": botdata['bearer'],
         "X-bot-id": botdata['botid'],
         "X-workspace-id": botdata['workspace_id']
     }
     response = requests.get(url, headers=headers)
     return json.loads(response.text)['bot']['integrations']
   
   def get_webchat_integration(self, auth_data):
     url = f"https://api.botpress.cloud/v1/admin/hub/integrations/{auth_data['integration_id']}"
     headers = {
         "accept": "application/json",
         "authorization": auth_data['bearer'],
         "x-bot-id": auth_data['botid'],
         "x-workspace-id": auth_data['workspace_id']
     }
     response = requests.get(url, headers=headers)
     return json.loads(response.text)
   
   def list_conversations_webchat(self, auth_data):
     url = "https://api.botpress.cloud/v1/chat/conversations"
     headers = {
         "authorization": auth_data['bearer'],
         "accept": "application/json",
         "x-integration-id": auth_data['integration_id'],
         "x-bot-id": auth_data['botid']
     }
     response = requests.get(url, headers=headers)
     return json.loads(response.text)
   
   def get_conversation(self, conversationid, auth_data):
     url = f"https://api.botpress.cloud/v1/chat/messages?conversationId={conversationid}"
     headers = {
         "authorization": auth_data['bearer'],
         "accept": "application/json",
         "x-integration-id": auth_data['integration_id'],
         "x-bot-id": auth_data['botid']
     }
     response = requests.get(url, headers=headers)
     return json.loads(response.text)
   
   def get_conversation_messages(self, auth_data):
     conversations = self.list_conversations_webchat(auth_data)
     conversation_map = {}
     conversations_list = []
     for conv in conversations['conversations']:
         conversation = self.get_conversation(conv['id'], auth_data)
         conversation_map[conv['id']] = conversation['messages']
         conversations_list.append(conversation_map)
     return conversations_list
   
   def group_messages_by_integration(self, botdata, integrations):
     all_messages = []
     for i in integrations:
         integration_data = {
             'name': integrations[i]['name'],
             'id': i
         }
         botd = self.update_botdata(botdata, i)
         conversations_messages = self.get_conversation_messages(botd)
         integration_data['messages'] = conversations_messages
         all_messages.append(integration_data)
     return all_messages
   
   def group_messages_by_conversation(self, data_grouped_by_integration):
     sorted_list = []
     for integration in data_grouped_by_integration:
         integration_name = integration['name']
         integration_id = integration['id']
         for message_dict in integration['messages']:
             for conversation_id, messages in message_dict.items():
                 sorted_list.append({
                     'conversation': conversation_id,
                     'integration_name': integration_name,
                     'integration_id': integration_id, 
                     'messages': messages
                 })
     return sorted_list
   
conversations = Conversations()
   
@socketio.on('data')
def handle_conversations(data):

   try:
     # Deserializar el mensaje JSON recibido
     botdata = json.loads(data)
   
     # Obtener integraciones
     integrations = conversations.get_bot_integrations(botdata)
     
     # Agrupar datos por integración
     grouped_data_integration = conversations.group_messages_by_integration(botdata, integrations)
     
     # Agrupar por conversación e integración
     data = conversations.group_messages_by_conversation(grouped_data_integration)
     
     # Serializar y enviar datos de vuelta al cliente
     emit(json.dumps({"event": "conversation_data", "data": data}), broadcast=True)
   
   except Exception as e:
     # Enviar mensaje de error en caso de excepción
     emit(json.dumps({"event": "error", "message": str(e)}), broadcast=True)


@socketio.on("connect")
def connected():
   """event listener when client connects to the server"""
   print(request.sid)
   print("client has connected")
   emit("connect",{"data":f"id: {request.sid} is connected"})
   
@socketio.on("disconnect")
def disconnected():
   """event listener when client disconnects to the server"""
   print("user disconnected")
   emit("disconnect",f"user {request.sid} disconnected",broadcast=True)

if __name__ == "__main__":
   socketio.run(app, debug=True,port=5000)


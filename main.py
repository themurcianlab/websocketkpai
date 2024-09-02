from flask import Flask
from flask_socketio import SocketIO, emit
import requests
import json

import asyncio
import http
import signal
import json
from websockets import WebSocketServerProtocol
from websockets.asyncio.server import serve

app = Flask(__name__)


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

async def handle_conversations(websocket: WebSocketServerProtocol):
   async for message in websocket:
       try:
           # Deserializar el mensaje JSON recibido
           botdata = json.loads(message)

           # Obtener integraciones
           integrations = conversations.get_bot_integrations(botdata)
           
           # Agrupar datos por integración
           grouped_data_integration = conversations.group_messages_by_integration(botdata, integrations)
           
           # Agrupar por conversación e integración
           data = conversations.group_messages_by_conversation(grouped_data_integration)
           
           # Serializar y enviar datos de vuelta al cliente
           await websocket.send(json.dumps({"event": "conversation_data", "data": data}))

       except Exception as e:
           # Enviar mensaje de error en caso de excepción
           await websocket.send(json.dumps({"event": "error", "message": str(e)}))

def health_check(connection, request):
   if request.path == "/healthz":
       return connection.respond(http.HTTPStatus.OK, "OK\n")

async def main():
   # Configurar el bucle de eventos para manejar SIGTERM
   loop = asyncio.get_running_loop()
   stop = loop.create_future()
   loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

   # Servidor WebSocket
   async with serve(
       handle_conversations,
       host="",
       port=8080,
       process_request=health_check,
   ):
       await stop

if __name__ == "__main__":
   asyncio.run(main())
   
 
# app = Flask(__name__)
# api = Api(app)
# CORS(app, resources={r"/*": {"origins": "*"}})
 
# class Conversations(Resource):
   
#     def update_botdata(self,botdata, new_integration_id):
#         botdata['integration_id'] = new_integration_id
#         return botdata

#     def get_bot_integrations(self,botdata) :
#         url = f"https://api.botpress.cloud/v1/admin/bots/{botdata['botid']}"

#         headers = {
#             "Accept": "application/json",
#             "Authorization": botdata['bearer'],
#             "X-bot-id": botdata['botid'],
#             "X-workspace-id": botdata['workspace_id']
#         }

#         response = requests.get(url, headers=headers)
#         return json.loads(response.text)['bot']['integrations']


#     def get_webchat_integration(self,auth_data):
#         #telegram: 
#         url = f"https://api.botpress.cloud/v1/admin/hub/integrations/{auth_data['integration_id']}"

#         headers = {
#             "accept": "application/json",
#             "authorization": auth_data['bearer'],
#             "x-bot-id": auth_data['botid'],
#             "x-workspace-id": auth_data['workspace_id']
#         }

#         response = requests.get(url, headers=headers)


#         return json.loads(response.text)

#     def list_conversations_webchat(self,auth_data):

#         url = "https://api.botpress.cloud/v1/chat/conversations"

#         headers = {
#             "authorization": auth_data['bearer'],
#             "accept": "application/json",
#             "x-integration-id": auth_data['integration_id'],
#             "x-bot-id": auth_data['botid']
#         }

#         response = requests.get(url, headers=headers)
#         return json.loads(response.text)

#     def get_conversation(self,conversationid, auth_data):

#         url = f"https://api.botpress.cloud/v1/chat/messages?conversationId={conversationid}"

#         headers = {
#             "authorization": auth_data['bearer'],
#             "accept": "application/json",
#             "x-integration-id": auth_data['integration_id'],
#             "x-bot-id": "1d074a47-43f9-40da-a042-4c755ab616ee"
#         }

#         response = requests.get(url, headers=headers)

#         return json.loads(response.text)

#     def get_conversation_messages(self,auth_data):
#         #"87b01760-ede8-49d5-afc6-6afc0d0d1bdb"
#         #webchat_int_id =
#         conversations = self.list_conversations_webchat(auth_data)

#         conversation_map = {}
#         conversations_list = []

#         for conv in conversations['conversations']:
#             conversation = self.get_conversation(conv['id'], auth_data)
#             conversation_map[conv['id']] = conversation['messages']
#             conversations_list.append(conversation_map)


#         return conversations_list


#     def group_messages_by_integration(self,botdata, integrations):

#         all_messages = []
#         integration_data = {}
#         for i in integrations:
#             integration_data['name'] = integrations[i]['name'] 
#             botd = self.update_botdata(botdata, i)
#             conversations_messages = self.get_conversation_messages(botd)
#             integration_data['messages'] = conversations_messages
#             integration_data['id'] = i
#             all_messages.append(integration_data)
#             integration_data = {}
#         return all_messages

#     def group_messages_by_conversation(self,data_grouped_by_integration):

#         # Crear la lista ordenada
#         sorted_list = []

#         # Iterar sobre cada integración en los datos
#         for integration in data_grouped_by_integration:
#             integration_name = integration['name']
#             integration_id = integration['id']
            
#             # Iterar sobre los mensajes de cada integración
#             for message_dict in integration['messages']:
#                 # Para cada conjunto de mensajes en el diccionario
#                 for conversation_id, messages in message_dict.items():
#                     sorted_list.append({
#                         'conversation': conversation_id,
#                         'integration_name': integration_name,
#                         'integration_id': integration_id, 
#                         'messages': messages
#                     })

#         # Mostrar la lista ordenada
#         return sorted_list
   
    
#    
#     def post(self,botdata):
#         # Obtain integrations
#         integrations = self.get_bot_integrations(botdata)
        
#         # Group data by integration
#         grouped_data_integration = self.group_messages_by_integration(botdata, integrations)
        
#         # Group by conversation and integration
#         data = self.group_messages_by_conversation(grouped_data_integration)

#          return data
 
   


 
# class UserOperations(Resource):
# #    BODY ESPERADO EN LA LLAMADA:
# #     {
# #     "headers": {
# #         "x-integration-id": "your_integration_id",
# #         "x-bot-id": "your_bot_id",
# #         "authorization": "your_bearer_token"
# #     },
# #     "bot_data": {
# #         // any bot-specific data if needed
# #     },
# #     "name": "John Doe",
# #     "message": "Hello, this is a test message.",
# #     "conversation_id": "conv_01J671EGTKY5W0E65KWDPG48HS"
# # }

#     def post(self):
#         # Parse the JSON request body
#         data = request.get_json()
        
#         # Extract headers and bot data from the request body
#         headers = data.get('headers')
#         bot_data = data.get('bot_data')
        
#         if not headers or not bot_data:
#             return {"message": "Missing required fields"}, 400

#         # Extract user data from the request body
#         name = data.get('name')
#         message = data.get('message')
#         conversation_id = data.get('conversation_id')

#         if not name or not message or not conversation_id:
#             return {"message": "Missing required fields"}, 400

#         # Set up headers for API requests
#         api_headers = {
#             "x-integration-id": headers.get("x-integration-id"),
#             "x-bot-id": headers.get("x-bot-id"),
#             "authorization": f"Bearer {headers.get('authorization')}",
#             "Content-Type": "application/json"
#         }

#         # Create a new user
#         user_response = self.create_user(name, api_headers)
#         if user_response:
#             user_id = user_response.get('user', {}).get('id')
#             if user_id:
#                 # Add the created user as a participant in a conversation
#                 participant_response = self.add_participant(conversation_id, user_id, api_headers)
#                 if participant_response:
#                     # Create a message in the conversation
#                     message_response = self.create_message(user_id, message, conversation_id, api_headers)
#                     return message_response

#         return {"message": "An error occurred"}, 500

#     def create_user(self, name, headers):
#         """
#         Creates a new user in Botpress.

#         Args:
#             name (str): The name of the user.
#             headers (dict): Headers for API requests.

#         Returns:
#             dict: The response from the API or None if an error occurred.
#         """
#         payload = {
#             "tags": {
#                 "webchat:id": headers.get("x-integration-id"),
#                 "id": headers.get("x-integration-id")
#             },
#             "name": name
#         }

#         try:
#             response = requests.post(
#                 f"https://api.botpress.cloud/v1/chat/users",
#                 headers=headers,
#                 json=payload
#             )
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             print(f"Error creating user: {e}")
#             return None

#     def add_participant(self, conversation_id, user_id, headers):
#         """
#         Adds a participant to a conversation.

#         Args:
#             conversation_id (str): The ID of the conversation.
#             user_id (str): The ID of the user to add.
#             headers (dict): Headers for API requests.

#         Returns:
#             dict: The response from the API or None if an error occurred.
#         """
#         payload = {
#             "userId": user_id
#         }

#         try:
#             response = requests.post(
#                 f"https://api.botpress.cloud/v1/chat/conversations/{conversation_id}/participants",
#                 headers=headers,
#                 json=payload
#             )
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             print(f"Error adding participant: {e}")
#             return None

#     def create_message(self, user_id, message, conversation_id, headers):
#         """
#         Creates a new message in a conversation.

#         Args:
#             user_id (str): The ID of the user sending the message.
#             message (str): The content of the message.
#             conversation_id (str): The ID of the conversation.
#             headers (dict): Headers for API requests.

#         Returns:
#             dict: The response from the API or None if an error occurred.
#         """
#         payload = {
#             "payload": {
#                 "text": message
#             },
#             "tags": {
#                 "webchat:id": headers.get("x-integration-id"),
#                 "id": headers.get("x-integration-id")
#             },
#             "userId": user_id,
#             "conversationId": conversation_id,
#             "type": "text"
#         }

#         try:
#             response = requests.post(
#                 f"https://api.botpress.cloud/v1/chat/messages",
#                 headers=headers,
#                 json=payload
#             )
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             print(f"Error creating message: {e}")
#             return None
        


# api.add_resource(UserOperations, '/user-operations/send')
# api.add_resource(Conversations, '/get_conversations')
# #api.add_resource(Conversations, '/conversations')

# if __name__ == '__main__':
#     app.run(app, debug=True)



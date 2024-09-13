from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from db.manager import ( GroupManager, UserManager, ChatManager, trimPhoneumber, sendCode, agreeCode )
from handler.Handler import Handler
from meta.encrypt import CryptoServer
from flask_cors import CORS
import time
import logging
import os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

logging.basicConfig(level=logging.INFO)

user_sessions = {}

@app.route('/api', methods=['POST'])
def api():
    try:
        data = request.get_json()
        user_manager = UserManager()
        chat_manager = ChatManager(user_manager=user_manager)
        handler = Handler(chatManager=chat_manager, userManager=user_manager)
        hash_get = CryptoServer(key=data['key'])
   
        result = handler.methodNum(method=hash_get.decrypt(data=data['method']), data=data['data'], hash=hash_get)

        if 'data_enc' in result.keys():
            return result
        else:
            raise ValueError(result['message'])
    
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return jsonify({'error': 'serverInternal', 'message': str(e)}), 500

@socketio.on('authenticate')
def handle_authenticate(data):
    try:
        username = data.get('username')
        token = data.get('token')
        user_manager = UserManager()
        
        if user_manager.authenticate_user(username=username, auth_token=token).get('status') == 'OK':
            user_sessions[username] = request.sid
            join_room(username)
            user_manager.online(username=username, auth_token=token, status='online')
            emit('authenticated', {'message': 'User authenticated', 'username': username}, to=request.sid)
        else:
            emit('authentication_failed', {'message': 'Authentication failed'}, to=request.sid)
            user_manager.online(username=username, auth_token=token, status='offline')
            logging.warning(f"Authentication failed for user {username}")
    except Exception as e:
        logging.error(f"An error occurred during authentication: {str(e)}")
        emit('error', {'message': 'Internal server error'}, to=request.sid)

@socketio.on("register")
def handle_register(data: dict):
    try:
        keys: list = list(data.keys())
        if not "fullname" in keys or not "username" in keys or not "phone_number" in keys:
            emit("error", {"message": "Invalid arguments - Not found arguments"})

        else:
            phone = trimPhoneumber(data.get("phone_number"))
            if not "code" in keys:
                objects = sendCode(phone)
                if not objects['error']:
                    if objects['ok']:
                        emit("registered", {"code_sended": True, "to_phone_number": phone}, to=request.sid)
                    else:emit("error", {"message": objects['message']}, to=request.sid)
                else:emit("error", {"message": objects['message']}, to=request.sid)
            else:
                objects = agreeCode(phone, data.get("code"))
                print("CODE ", objects)
                if not objects['error']:
                    if objects['ok']:
                        user_manager = UserManager()
                        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
                        
                        result = handler.register(data.get("username"), phone, data.get("fullname"), data.get("profile", None), data.get("bio", None))
                        if result['status'] == "OK":
                            del result['status']
                            emit("registered", result['user'], to=request.sid)
                        else:emit("error", {"message": result['status']}, to=request.sid)
                    else:emit("error", {"message": result['message']}, to=request.sid)
                else:emit("error", {"message": result['message']}, to=request.sid)

    except Exception as ERROR:
        emit("error", {"message": str(ERROR)}, to=request.sid)

@socketio.on("login")
def handle_login(data: dict):
    try:
        user_manager = UserManager()
        keys: list = list(data.keys())
        if not "username" in keys or not "token" in keys or not "phone_number" in keys:
            emit("error", {"message": "Invalid arguments - Not found arguments"})
        else:
            phone = trimPhoneumber(data.get("phone_number"))
            if not "code" in keys:
                objects = sendCode(phone)
                if not objects['error']:
                    if objects['ok']:
                        emit("logined", {"code_sended": True, "to_phone_number": phone}, to=request.sid)
                    else:emit("error", {"message": objects['message']}, to=request.sid)
                else:emit("error", {"message": objects['message']}, to=request.sid)
            else:
                objects = agreeCode(phone, data.get("code"))
                if not objects['error']:
                    if objects['ok']:
                        user_manager = UserManager()
                        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
                        
                        result = handler.login(data.get("username"), data.get("token"), data.get("phone_number"))
                        if result['status'] == "OK":
                            del result['status']
                            emit("logined", result['user'], to=request.sid)
                        else:emit("error", {"message": result['status']}, to=request.sid)
                    else:emit("error", {"message": result['message']}, to=request.sid)
                else:emit("error", {"message": result['message']}, to=request.sid)

    except Exception as ERROR:
        emit("error", {"message": str(ERROR)}, to=request.sid)

@socketio.on("getUserInfo")
def handle_user_info(data: dict):
    try:
        user_manager = UserManager()
        username = data.get('username')
        token = data.get('token')
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        result = handler.getUserInfo(username, token)

        if not result['status'] == "OK":emit("error", {"message": result['status']})
        else:emit("user_info", result, to=request.sid)

    except Exception as ERROR:
        emit("error", {"message": str(ERROR)}, to=request.sid)

@socketio.on("getUsernameByID")
def handle_username_by_id(data: dict):
    try:
        user_manager = UserManager()
        username = data.get('username')
        token = data.get('token')
        user_id = data.get("user_id", "")
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        result = handler.getUsernameByID(username, token, user_id)

        if not result['status'] == "OK":emit("error", {"message": result['status']})
        else:emit("username_info", result['user'], to=request.sid)

    except Exception as ERROR:
        emit("error", {"message": str(ERROR)}, to=request.sid)

@socketio.on("getChat")
def on_chat_user(data: dict):
    try:
        user_manager = UserManager()
        username = data.get('username')
        target_user = data.get('target_user')
        token = data.get('token')
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        result = handler.getChatsUser(username, target_user, token)
        if not result['status'] == "OK":emit("error", {"message": result})
        else:emit("getChat", result['result'], to=request.sid)
    except Exception as ERROR:
        emit("error", {"message": str(ERROR)}, to=request.sid)

@socketio.on("getChats")
def on_chats(data: dict):
    try:
        user_manager = UserManager()
        username = data.get('username')
        token = data.get('token')
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        result = handler.getChats(username, token)
        if not result['status'] == "OK":emit("error", {"message": result['status']})
        else:emit("getChats", result['result'], to=request.sid)
    except Exception as ERROR:
        emit("error", {"message": str(ERROR)}, to=request.sid)

@socketio.on("getGroupMembers")
def get_members_list(data: dict):
    try:
        user_manager = UserManager()
        group_name = data.get("group_name", "")
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        result = handler.getMembersList(group_name)

        if not result['status'] == "OK":emit("error", {"message": result['status']})
        else:emit("group_members", result['members'], to=request.sid)

    except Exception as ERROR:
        emit("error", {"message": str(ERROR)}, to=request.sid)

@socketio.on("editMessages")
def on_edit_messages(data: dict):
    try:
        user_manager = UserManager()
        username = data.get('username')
        token = data.get('token')
        to_user = data.get("to")
        message_id = data.get("message_id")
        new_message = data.get("new_message")
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        result = handler.editMessages(username, token, to_user, message_id, new_message)

        if not result['status'] == "OK":emit("error", {"message": result['status']})
        else:emit("edited_message", {"to": to_user, "message_id": message_id, "new_message": new_message, "edited_on": time.ctime(time.time())}, to=request.sid)

    except Exception as ERROR:
        emit("error", {"message": str(ERROR)}, to=request.sid)

@socketio.on("getMessages")
def handle_messages(data: dict):
    try:
        user_manager = UserManager()
        username = data.get('username')
        token = data.get('token')
        user = data.get("user", "")
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        result = handler.getMessages(username, token, user)

        if not result['status'] == "OK":emit("error", {"message": result['status']})
        else:emit("messages", result['messages'], to=request.sid)

    except Exception as ERROR:
        emit("error", {"message": str(ERROR)}, to=request.sid)

@socketio.on("updateProfile")
def handle_profile(data: dict):
    try:
        user_manager = UserManager()
        username = data.get('username')
        token = data.get('token')
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        result = handler.update_profile(username, token, data)

        if not result['status'] == "OK":emit("error", {"message": result['status']})
        else:emit("updated_profile", result['user'], to=request.sid)

    except Exception as ERROR:
        emit("error", {"message": str(ERROR)}, to=request.sid)

@socketio.on("getChatsGroup")
def on_group_chats(data: dict):
    try:
        user_manager = UserManager()
        username = data.get('username')
        token = data.get('token')
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        result = handler.getChatsGroup(username, token)

        if not result['status'] == "OK":emit("error", {"message": result['status']})
        else:emit("messages", result['data'], to=request.sid)

    except Exception as ERROR:
        emit("error", {"message": str(ERROR)}, to=request.sid)

@socketio.on("addMemberToGroup")
def handle_add_member(data: dict):
    try:
        user_manager = UserManager()
        username = data.get('username')
        token = data.get('token')
        group_name = data.get("group_name")
        target = data.get("target_username")
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        result = handler.addMemberToGroup(username, token, group_name, target)

        if not result['status'] == "OK":emit("error", {"message": result['status']})
        
        else:
            emit("in_chat_member", result['data'], to=request.sid)

    except Exception as ERROR:
        emit("error", {"message": str(ERROR)}, to=request.sid)

@socketio.on("removeMemberGroup")
def handle_add_member(data: dict):
    try:
        user_manager = UserManager()
        username = data.get('username')
        token = data.get('token')
        group_name = data.get("group_name")
        target = data.get("target_username")
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        result = handler.removeMemberGroup(username, token, group_name, target)

        if not result['status'] == "OK":emit("error", {"message": result['status']})
        else:emit("in_chat_left_member", result['data'], to=request.sid)

    except Exception as ERROR:
        emit("error", {"message": str(ERROR)}, to=request.sid)

@socketio.on("addGroup")
def handle_add_group(data: dict):
    try:
        user_manager = UserManager()
        username = data.get('username')
        token = data.get('token')
        group_name = data.get("group_name")
        profile = data.get("profile_photo", None)
        bio = data.get("bio", None)
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        result = handler.addGroup(username, token, group_name, profile, bio)

        if not result['status'] == "OK":emit("error", {"message": result['status']})
        else:emit("group_creator", result['data'], to=request.sid)

    except Exception as ERROR:
        emit("error", {"message": str(ERROR)}, to=request.sid)

@socketio.on('markAsRead')
def handle_mark_as_read(data):
    try:
        user_manager = UserManager()
        username = data.get('username')
        token = data.get('token')
        target_user = data.get('target_user')
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        
        result = handler.mark_messages_as_read(username=username, token=token, target_user=target_user)
        user_manager.online(username=username, auth_token=token, status='online')
        emit('messages_marked_as_read', result, to=request.sid)
    except Exception as e:
        emit('error', {'message': {"message": str(e)}})

@socketio.on('sendMessage')
def handle_send_private_message(data):
    user_manager = UserManager()
    chat_manager = ChatManager(user_manager=user_manager)
    handler = Handler(chatManager=chat_manager, userManager=user_manager)

    try:
        from_user = data.get('from')
        to_user = data.get('to')


        if from_user in user_sessions and to_user in user_sessions:
            result = handler.handle_send_message(data)
            
            if result['status'] == 'success':
                print(f'\033[31m|| SID :: {request.sid} || DATA ::: {data} || TO ::: {to_user} || FROM_USER ::: {from_user} || {user_sessions}')
                socketio.emit(f'receive_private_message', result['data'], room=to_user)
                socketio.emit(f'receive_private_message', result['data'], room=from_user)
            else:
                logging.error(f"Message handling error: {result['message']}")
        else:
            print(f'Offline Users {user_sessions}')
            result = handler.handle_send_message(data)
            socketio.emit(f'offline', result['data'], room=from_user, to=request.sid)

    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        socketio.emit("error", {"message": str(e)})

@socketio.on('sendGroupMessage')
def handle_send_group_message(data):
    user_manager = UserManager()
    chat_manager = ChatManager(user_manager=user_manager)

    handler = Handler(chatManager=chat_manager, userManager=user_manager)

    try:
        from_user = data.get('from')
        group_name = data.get('group')

        if from_user in user_sessions and group_name in user_sessions:
            result = handler.handle_send_group_message(data)
            
            if result['status'] == 'success':
                for member in user_sessions:
                    socketio.emit('receive_group_message', result['data'], room=member)
            else:
                logging.error(f"Message handling error: {result['message']}")
        else:
            result = handler.handle_send_group_message(data)
            socketio.emit(f'offline', result['data'], room=from_user)

    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")

@socketio.on('getGroupMessages')
def handle_get_group_messages(data):
    try:
        user_manager = UserManager()
        username = data.get('username')
        token = data.get('token')
        group_name = data.get('group')
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        
        result = handler.getGroupMessages(username=username, token=token, group_name=group_name)
        if result['status'] == 'OK':
            emit('group_messages', result['data'], to=request.sid)
        else:
            emit('error', {'message': result['status']}, to=request.sid)
    
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on("addMemberToGroup")
def handle_add_member(data):
    try:
        user_manager = UserManager()
        username = data.get('username')
        token = data.get('token')
        group_name = data.get('group_name')
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        
        result = handler.getGroupMessages(username=username, token=token, group_name=group_name)
        if result['status'] == 'OK':
            emit('group_messages', result['data'], to=request.sid)
        else:
            emit('error', {'message': result['status']}, to=request.sid)
    
    except Exception as e:
        logging.error(f"Error in handle_get_group_messages: {str(e)}")
        emit('error', {'message': str(e)})

@socketio.on('typing')
def typingHandler(data):
    try:
        print(user_sessions)
        emit('typing', {
            'typing': 'Typing is...'
        }, to=user_sessions[data.get('target')])
    except Exception as e:
        logging.error(f"Error in typingError: {str(e)}")
        emit('error', {'message': str(e)})

@socketio.on("searchUserByUsername")
def searching_handler(data: dict):
    try:
        user_manager = UserManager()
        username = data.get('username')
        token = data.get('token')
        user_name = data.get('user_username')
        handler = Handler(chatManager=ChatManager(UserManager()), userManager=user_manager)
        
        result = handler.searchUserByUsername(username=username, token=token, user_username=user_name)
        if result['status'] == "OK":
            emit("researched_users", result['user'], to=request.sid)
        else:
            emit("error", {"message": result['status']})
    except Exception as ERROR:
        err = str(ERROR)
        logging.error(f"Error in searching_handler: {err}")
        emit("error", {"message": err})

@socketio.on('connect')
def handle_connect():
    logging.info(f"Client connected with SID: {request.sid}")
    emit('handshake', {'message': 'connect'}, to=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    logging.info(f"Client disconnected. SID: {request.sid}")
    for username, sid in user_sessions.items():
        if sid == request.sid:
            leave_room(username)
            logging.info(f"User {username} disconnected and left room")
            del user_sessions[username]
            break

if __name__ == '__main__':
    socketio.run(app, debug=True, host='127.0.0.1', port=8080)
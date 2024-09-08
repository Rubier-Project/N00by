import socketio
import base64
import os

# addMemberToGroup
# removeMemberGroup
# sendGroupMessage -> Didnt return data


# updateProfile
# editMessages

# Server URL
SERVER_URL = 'http://127.0.0.1:8080'


sio = socketio.Client()

username = 'MobinX'
token = '9DqZhNbWmj_B30VB4tVWqOC2pAkBryCZCX5Xv9SWFOk'

@sio.event
def connect():
    print('Connection established')
    #sio.emit('sendGroupMessage', {"username": "alzize", "token": "6KoLCeLNKkZNjqi8e8fDcvxSJVWJYwT4oSEVBIvDimw", "from": "alzzie", "group": "babat", "message": "hi"})
    #sio.emit('getGroupMessages', {"username": "alzize", "token": "6KoLCeLNKkZNjqi8e8fDcvxSJVWJYwT4oSEVBIvDimw", "group": "babat"})
    #sio.emit("connect")
    #sio.emit("disconnect")
    #sio.emit("getUsernameByID", {"username": "alzize", "token": "6KoLCeLNKkZNjqi8e8fDcvxSJVWJYwT4oSEVBIvDimw", "user_id": "alzzie"})
    #sio.emit("getGroupMembers", {"username": "alzize", "token": "6KoLCeLNKkZNjqi8e8fDcvxSJVWJYwT4oSEVBIvDimw", "group_name": "babat"})
    #sio.emit("sendMessage", {"username": "alzize", "token": "6KoLCeLNKkZNjqi8e8fDcvxSJVWJYwT4oSEVBIvDimw", "from": "alzize", "to": "alzzie", "message": "HELLO WORLD2 z"})

# @sio.on("registered")
# def on_registered(data):
#     print(data)

# @sio.on("registered")
# def on_login(data):
#     print(data)

@sio.on("group_messages")
def on_login(data):
    print(data)

@sio.on("receive_group_message")
def on_message(data):
    print(data)

@sio.on("handshake")
def on_handshake(data):
    print(data)

@sio.on("user_info")
def on_info(data):
    print(data)

@sio.on("username_info")
def on_username_info(data):
    print(data)

@sio.on("group_members")
def on_members(data):
    print(data)

@sio.on("offline")
def on_offlines(data):
    print(data)

@sio.on("receive_private_message")
def on_rpm(data):
    print(data)

@sio.on("error")
def on_error(data):
    print(f"Error: {data}")

sio.connect(SERVER_URL)

sio.wait()

x = """
{'username': 'alzize', 'phone': '09904541580', 'fullname': 'alie', 'status': 'o
nline', 'bio': None, 'profile': 'https://www.google.com/url?sa=i&url=https%3A%2
F%2Fstock.adobe.com%2Fimages%2Fdefault-avatar-profile-flat-icon-social-media-us
er-vector-portrait-of-unknown-a-human-image%2F353110097&psig=AOvVaw3CkGCCeJAqiq
KqgZ_mMS0G&ust=1722945658368000&source=images&cd=vfe&opi=89978449&ved=0CBEQjRxq
FwoTCNie4Ojm3YcDFQAAAAAdAAAAABAK', 'very': 'user', 'token': '6KoLCeLNKkZNjqi8e8
fDcvxSJVWJYwT4oSEVBIvDimw', 'have_tick': False}

{'status': 'OK', 'group': {'group_name': 'babat', 'profile': 'https://encrypted
-tbn0.gstatic.com/images?q=tbn:ANd9GcRFEZSqk8dJbB0Xc-fr6AWv2aocxDdFpN6maQ&', 'b
io': 'نه'}}

{'status': 'OK', 'users': [{'username': 'alzie', 'last_message': 'N/A', 'last_t
ime': 'N/A', 'profile': 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fstoc
k.adobe.com%2Fimages%2Fdefault-avatar-profile-flat-icon-social-media-user-vecto
r-portrait-of-unknown-a-human-image%2F353110097&psig=AOvVaw3CkGCCeJAqiqKqgZ_mMS
0G&ust=1722945658368000&source=images&cd=vfe&opi=89978449&ved=0CBEQjRxqFwoTCNie
4Ojm3YcDFQAAAAAdAAAAABAK', 'count_message': 0, 'status': 'online', 'admin': 'us
er'}, {'username': 'alzzie', 'last_message': 'N/A', 'last_time': 'N/A', 'profil
e': 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fstock.adobe.com%2Fimages
%2Fdefault-avatar-profile-flat-icon-social-media-user-vector-portrait-of-unknow
n-a-human-image%2F353110097&psig=AOvVaw3CkGCCeJAqiqKqgZ_mMS0G&ust=1722945658368
000&source=images&cd=vfe&opi=89978449&ved=0CBEQjRxqFwoTCNie4Ojm3YcDFQAAAAAdAAAA
ABAK', 'count_message': 0, 'status': 'online', 'admin': 'user'}]}

"""
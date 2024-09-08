import socketio
import base64
import os

# Server URL
SERVER_URL = 'http://127.0.0.1:8080'


sio = socketio.Client()

username = 'MobinX'
token = '9DqZhNbWmj_B30VB4tVWqOC2pAkBryCZCX5Xv9SWFOk'

@sio.event
def connect():
    print('Connection established')
    sio.emit("register", {"fullname": "pedaret", "username": "Are", "phone_number": "+989904541580"})
    #sio.emit('getMessages', {"token": "gCBP8Clni7oC53Z9w18gPp40NNhF742jv9mxzHpwzpg", "username": "alzzie", "user": "alzize"})

@sio.on("registered")
def on_reg(data):
    print(data)

@sio.on("logined")
def on_log(data):
    print(data)

@sio.on("messages")
def on_messages(data):
    print(data)

@sio.on("error")
def on_error(data):
    print(f"Error: {data}")

sio.connect(SERVER_URL)

sio.wait()

x = """

{'username': 'alzzie', 'phone': '09904541580', 'fullname': 'eeeeeee', 'status':
 'online', 'bio': None, 'profile': 'https://www.google.com/url?sa=i&url=https%3
A%2F%2Fstock.adobe.com%2Fimages%2Fdefault-avatar-profile-flat-icon-social-media
-user-vector-portrait-of-unknown-a-human-image%2F353110097&psig=AOvVaw3CkGCCeJA
qiqKqgZ_mMS0G&ust=1722945658368000&source=images&cd=vfe&opi=89978449&ved=0CBEQj
RxqFwoTCNie4Ojm3YcDFQAAAAAdAAAAABAK', 'very': 'user', 'token': 'gCBP8Clni7oC53Z
9w18gPp40NNhF742jv9mxzHpwzpg', 'have_tick': False}
"""
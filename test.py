import socketio

sio = socketio.Client()



@sio.event
def connect():
    print('Connected to server as User1')
    sio.emit('authenticate', data={'username': 'CipherX', 'token': 'LliwiDOg7G1t8Wr9Ll0-OPzh7pwWz25noJrCAsLRalw'})
    getUser('CipherX', 'LliwiDOg7G1t8Wr9Ll0-OPzh7pwWz25noJrCAsLRalw')
    getChat('CipherX', '12', 'LliwiDOg7G1t8Wr9Ll0-OPzh7pwWz25noJrCAsLRalw')
    #send_messages() 

@sio.event
def receive_private_message(data):
    print(f"User1 received: {data['message']}")

@sio.event
def authenticated(data):
    print(data)

@sio.event
def error(data):
    print(data)


@sio.event
def chats(data):
    print("GetChats : ")

@sio.event
def user_info(data):
    print("users : ",)

@sio.event
def getChat(data):
    print("getChat : ", data)

@sio.event
def disconnect():
    print('Disconnected from server')


def getChats(username, token):
    sio.emit('getChats', {'username': username, 'token': token})

def getChat(username, target_user, token):
    sio.emit('getChat', {'username': username, 'target_user': target_user, 'token': token})

def getUser(username, token):
    sio.emit('getUserInfo', {'username': username, 'token': token})


def send_messages():
    while True:
        message = input("Enter your message: ")
        if message.lower() == 'exit':
            break 
        sio.emit('sendMessage', {
            'from': 'CipherX',
            'to': 'X1',
            'message': message
        })

sio.connect('http://127.0.0.1:8080')
sio.wait()

import socketio


sio = socketio.Client()


@sio.event
def connect():
    print('Connected to server as User1')
    sio.emit('authenticate', data={'username': 'X1', 'token': 'LliwiDOg7G1t8Wr9Ll0-OPzh7pwWz25noJrCAsLRalw'})
    getChats('X1', 'LliwiDOg7G1t8Wr9Ll0-OPzh7pwWz25noJrCAsLRalw')
    send_messages() 

@sio.event
def receive_private_message(data):
    print(f"User1 received: {data['message']}")

@sio.event
def authenticated(data):
    print(data)

def getChats(username, token):
    sio.emit('getChats', {'username': username, 'token': token})

@sio.event
def chats(data):
    print("GetChats : ", data)

@sio.event
def disconnect():
    print('Disconnected from server')

def send_messages():
    while True:
        message = input("Enter your message: ")
        if message.lower() == 'exit':
            break 
        sio.emit('sendMessage', {
            'from': 'X1',
            'to': 'CipherX',
            'message': message
        })

sio.connect('http://127.0.0.1:8080')
sio.wait()

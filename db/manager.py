import sqlite3
import secrets
import requests
from datetime import datetime

lisence = "e765defd954e1e682c81ab4956f5df00"
reflex_api = f"http://api-free.ir/api2/very?token={lisence}&phone="


def trimPhoneumber(number: int) -> str:
    num = str(number).strip()

    if num.startswith("0"):num = number[1:]
    elif num.startswith("98"):num = number[2:]
    elif num.startswith("+98"):num = number[3:]
    else:num = number

    return "0"+num

def sendCode(phone: str):
    try:
        data = requests.post(reflex_api+phone)
        print(data.text)
        data = data.json()
        data['error'] = False
        return data
    
    except Exception as ERROR_CONNECTION:
        return {
            "error": True,
            "message": str(ERROR_CONNECTION)
        }
    
def agreeCode(phone: str, code: str):
    try:
        data = requests.post(reflex_api+phone+"&code="+code).json()
        data['error'] = False
        return data
    
    except Exception as ERROR_CONNECTION:
        return {
            "error": True,
            "message": str(ERROR_CONNECTION)
        }

class Database:
    def __init__(self):
        self.connection = sqlite3.connect('chat_app.db', timeout=10, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        with self.connection:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    phone TEXT,
                    fullname TEXT,
                    status TEXT,
                    bio TEXT,
                    profile TEXT,
                    very TEXT,
                    token TEXT,
                    unread_count TEXT
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    from_user TEXT,
                    to_user TEXT,
                    message TEXT,
                    timestamp TEXT,
                    message_id TEXT PRIMARY KEY,
                    reply_data TEXT
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    group_name TEXT PRIMARY KEY,
                    profile TEXT,
                    bio TEXT
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_messages (
                    group_name TEXT,
                    from_user TEXT,
                    message TEXT,
                    timestamp TEXT,
                    message_id TEXT PRIMARY KEY
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_members (
                    group_name TEXT,
                    username TEXT,
                    PRIMARY KEY (group_name, username)
                )
            ''')

    def close(self):
        self.connection.close()

class UserManager:
    def __init__(self):
        self.db = Database()
        self.chat_manager = ChatManager(self)

    def add_user(self, username, phone, fullname, bio, profile=None):
        default_profile = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRFEZSqk8dJbB0Xc-fr6AWv2aocxDdFpN6maQ&'
        if profile is None or profile.strip() == '':
            profile = default_profile

        try:
            is_username = self.username_access(username)['status']
            # is_phone = self.phone_access(trimPhoneumber(phone))['status']

            if is_username == "OK":
                return {"status": "USERNAME_EXISTS"}
            
            # if is_phone == "OK":
            #     return {"status": "PHONE_NUMBER_EXISTS"}

            auth_token = self.generate_auth_token()
            with self.db.connection:
                self.db.cursor.execute('''
                    INSERT INTO users (username, phone, fullname, status, bio, profile, very, token)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (username, trimPhoneumber(phone), fullname, 'online', bio, profile, 'user', auth_token))
                self.db.connection.commit()
                self.chat_manager.initialize_user_messages(username)
            return {'status': 'OK', 'user': {'username': username, 'phone': phone, 'fullname': fullname, 'status': 'online', 'bio': bio, 'profile': profile, 'very': 'user', 'token': auth_token, "have_tick": False}}
        except sqlite3.IntegrityError:
            return {'status': 'USERNAME_INVALID'}

    def update_profile(self, username, auth_token, fullname=None, bio=None, profile=None):
        if self.authenticate_user(username, auth_token)['status'] == 'OK':
            with self.db.connection:
                query = 'UPDATE users SET '
                params = []
                if fullname:
                    query += 'fullname = ?, '
                    params.append(fullname)
                if bio:
                    query += 'bio = ?, '
                    params.append(bio)
                if profile:
                    query += 'profile = ?, '
                    params.append(profile)
                query = query.rstrip(', ')
                query += ' WHERE username = ? AND token = ?'
                params.extend([username, auth_token])
                self.db.cursor.execute(query, params)
                self.db.connection.commit()
            return {'status': 'OK', 'user': {'username': username, 'fullname': fullname, 'bio': bio, 'profile': profile}}
        else:
            return {'status': 'TOKEN_INVALID | NOT_FOUND', 'user': {}}

    def online(self, username, auth_token, status='offline'):
        if self.authenticate_user(username, auth_token)['status'] == 'OK':
            with self.db.connection:
                self.db.cursor.execute('UPDATE users SET status = ? WHERE username = ? AND token = ?', (status, username, auth_token))
                self.db.connection.commit()
            return {'status': 'OK', 'user': {'username': username, 'status': status}}
        else:
            return {'status': 'TOKEN_INVALID | NOT_FOUND', 'user': {}}

    def authenticate_user(self, username, auth_token):
        self.db.cursor.execute('SELECT * FROM users WHERE username = ? AND token = ?', (username, auth_token))
        user = self.db.cursor.fetchone()
        if user:
            #print(user)
            return {'status': 'OK', 'user': {'username': username}}
        else:
            return {'status': 'TOKEN_INVALID | NOT_FOUND', 'user': {}}
        
    def username_access(self, username: str):
        self.db.cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = self.db.cursor.fetchone()
        if user:
            return {'status': 'OK', 'user': {'username': username}}
        else:
            return {'status': 'TOKEN_INVALID | NOT_FOUND', 'user': {}}

    def phone_access(self, phone: str):
        self.db.cursor.execute('SELECT * FROM users WHERE phone = ?', (trimPhoneumber(phone),))
        user = self.db.cursor.fetchone()
        if user:
            return {'status': 'OK', 'user': {'phone': phone}}
        else:
            return {'status': 'TOKEN_INVALID | NOT_FOUND', 'user': {}}

    def login(self, username, auth_token, phone_number):
        self.db.cursor.execute('SELECT * FROM users WHERE username = ? AND token = ? AND phone = ?', (username, auth_token, trimPhoneumber(phone_number)))
        user = self.db.cursor.fetchone()
        if user:
            return {'status': 'OK', 'user': {'username': username}}
        else:
            return {'status': 'TOKEN_INVALID | NOT_FOUND', 'user': {}}

    def getUsernameByID(self, username, auth_token, getUser):
        if self.authenticate_user(username, auth_token)['status'] == 'OK':
            self.db.cursor.execute('SELECT * FROM users WHERE username = ?', (getUser,))
            user = self.db.cursor.fetchone()
            if user:
                return {'status': 'OK', 'user': {'fullname': user[2], 'bio': user[4], 'username': getUser, 'profile': user[5], 'status': user[3], 'admin': user[6]}}
            else:
                return {'status': 'USER_NOT_FOUND', 'user': {}}
        else:
            return {'status': 'TOKEN_INVALID | NOT_FOUND', 'user': {}}

    def generate_auth_token(self):
        return secrets.token_urlsafe()

    def user_exists(self, username):
        self.db.cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
        return self.db.cursor.fetchone() is not None

class ChatManager:
    def __init__(self, user_manager):
        self.user_manager = user_manager
        self.db = user_manager.db

    def increment_unread_message_count(self, to_user, from_user):
        self.db.cursor.execute('SELECT COUNT(*) FROM messages WHERE to_user = ? AND from_user = ?', (to_user, from_user))
        count = self.db.cursor.fetchone()[0]
        with self.db.connection:
            self.db.cursor.execute('UPDATE users SET unread_count = ? WHERE username = ?', (count, to_user))
            self.db.connection.commit()
        return count

    def reset_unread_message_count(self, username):
        with self.db.connection:
            self.db.cursor.execute('UPDATE users SET unread_count = 0 WHERE username = ?', (username,))
            self.db.connection.commit()
        return {'status': 'OK'}

    def getUserList(self, username, auth_token):
        if self.user_manager.authenticate_user(username, auth_token)['status'] == 'OK':
            self.db.cursor.execute('SELECT * FROM users WHERE username != ?', (username,))
            users = self.db.cursor.fetchall()
            enriched_users_list = []
            for user in users:
                enriched_user = {
                    "username": user[0],
                    "last_message": "N/A",
                    "last_time": "N/A",
                    "profile": user[5],
                    "count_message": 0,
                    "status": user[3],
                    "admin": user[6]
                }
                enriched_users_list.append(enriched_user)
            return {'status': 'OK', 'users': enriched_users_list}
        else:
            return {'status': 'TOKEN_INVALID | NOT_FOUND', 'users': {}}

    def getMessages(self, username, auth_token, user):
        if self.user_manager.authenticate_user(username, auth_token)['status'] == 'OK':
            self.db.cursor.execute('SELECT * FROM messages WHERE from_user = ? AND to_user = ?', (username, user))
            messages = self.db.cursor.fetchall()
            return {'status': 'OK', 'messages': messages}
        else:
            return {'status': 'TOKEN_INVALID | NOT_FOUND', 'user': {}}

    def initialize_user_messages(self, username):
        # Initialize user messages if needed
        pass

    def edit_message(self, username, token, message_id, to_user, new_message):
        if self.user_manager.authenticate_user(username, token)['status'] == 'OK':
            with self.db.connection:
                self.db.cursor.execute('UPDATE messages SET message = ? WHERE message_id = ? AND from_user = ? AND to_user = ?', (new_message, message_id, username, to_user))
                self.db.connection.commit()
            return {'status': 'OK', 'message': 'editMessage'}
        else:
            return {'status': 'TOKEN_INVALID | NOT_FOUND'}

    def add_private_message(self, from_user, to_user, message, timestamp=None, message_id=None, reply_data=None):
        if not self.user_manager.user_exists(to_user):
            print(f"User {to_user} does not exist")
            return
        if message_id is None:
            message_id = secrets.token_urlsafe()
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        with self.db.connection:
            self.db.cursor.execute('''
                INSERT INTO messages (from_user, to_user, message, timestamp, message_id, reply_data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (from_user, to_user, message, timestamp, message_id, reply_data))
            self.db.connection.commit()
        self.increment_unread_message_count(to_user, from_user)
        return {'status': 'OK', 'message': 'Message sent'}

class GroupManager:
    def __init__(self, user_manager):
        self.user_manager = user_manager
        self.db = user_manager.db

    def create_group(self, group_name, profile=None, bio=None):
        default_profile = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRFEZSqk8dJbB0Xc-fr6AWv2aocxDdFpN6maQ&'
        if profile is None or profile.strip() == '':
            profile = default_profile

        with self.db.connection:
            try:
                self.db.cursor.execute('''
                    INSERT INTO groups (group_name, profile, bio)
                    VALUES (?, ?, ?)
                ''', (group_name, profile, bio))
                self.db.connection.commit()
                return {'status': 'OK', 'group': {'group_name': group_name, 'profile': profile, 'bio': bio}}
            except sqlite3.IntegrityError:
                return {'status': 'GROUP_ALREADY_EXISTS'}

    def add_group_message(self, group_name, from_user, message, timestamp=None, message_id=None):
        if not self.user_manager.user_exists(from_user):
            print(f"User {from_user} does not exist")
            return
        if message_id is None:
            message_id = secrets.token_urlsafe()
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        with self.db.connection:
            self.db.cursor.execute('''
                INSERT INTO group_messages (group_name, from_user, message, timestamp, message_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (group_name, from_user, message, timestamp, message_id))
            self.db.connection.commit()
        return {'status': 'OK', 'message': 'Message sent'}

    def get_group_messages(self, group_name):
        self.db.cursor.execute('SELECT * FROM group_messages WHERE group_name = ?', (group_name,))
        messages = self.db.cursor.fetchall()
        message_list = []

        for message in messages:
            data = {
                "group_name": message[0],
                "from": message[1],
                "text": message[2],
                "time": message[3],
                "message_id": message[4]
            }
            message_list.append(data)

        return {'status': 'OK', 'messages': message_list}

    def add_member_to_group(self, group_name, username):
        if not self.user_manager.user_exists(username):
            print(f"User {username} does not exist")
            return
        with self.db.connection:
            try:
                self.db.cursor.execute('''
                    INSERT INTO group_members (group_name, username)
                    VALUES (?, ?)
                ''', (group_name, username))
                self.db.connection.commit()
                return {'status': 'OK'}
            except sqlite3.IntegrityError:
                return {'status': 'USER_ALREADY_IN_GROUP'}

    def remove_member_from_group(self, group_name, username):
        with self.db.connection:
            self.db.cursor.execute('''
                DELETE FROM group_members WHERE group_name = ? AND username = ?
            ''', (group_name, username))
            self.db.connection.commit()
        return {'status': 'OK'}

    def get_group_members(self, group_name):
        self.db.cursor.execute('SELECT username FROM group_members WHERE group_name = ?', (group_name,))
        members = self.db.cursor.fetchall()
        return {'status': 'OK', 'members': [member[0] for member in members]}

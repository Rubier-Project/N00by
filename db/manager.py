import sqlite3
import secrets
import requests
from datetime import datetime

lisence = "e765defd954e1e682c81ab4956f5df00"
reflex_api = f"http://api-free.ir/api2/very?token={lisence}&phone="


def trimPhoneumber(number: int) -> str:
    num = str(number).strip()
    if num.startswith("0"): num = num[1:]
    elif num.startswith("98"): num = num[2:]
    elif num.startswith("+98"): num = num[3:]
    else: num = num
    return "0" + num

def sendCode(phone: str):
    try:
        data = requests.post(reflex_api + phone)
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
        data = requests.post(reflex_api + phone + "&code=" + code).json()
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

    def create_table_user(self, username):
        with self.connection:
            self.cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS user_{username} (
                            list_chat TEXT
                            chats TEXT
                        )
                                ''')
            
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
                    CREATE TABLE IF NOT EXISTS user_chats (
                        username TEXT PRIMARY KEY,
                        chats TEXT
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
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_unread_counts (
                    username TEXT PRIMARY KEY,
                    unread_count INTEGER
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
        authCheck = self.authenticate_user(username, auth_token)
        if authCheck['status'] == 'OK':
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
            return {
                'status': 'OK', 
                'user': 
                {
                    'username': username, 
                    'auth': auth_token, 
                    'fullname': user[2], 
                    'status': user[3],
                    'phone_number': user[1],
                    'bio': user[4],
                    'profile': user[5],
                    'very': user[6]
                }
            }
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

import json

class ChatManager:
    def __init__(self, user_manager):
        self.user_manager = user_manager
        self.db = user_manager.db

    def _get_chats(self, username):
        self.db.cursor.execute('''
            SELECT chats FROM user_chats WHERE username = ?
        ''', (username,))
        result = self.db.cursor.fetchone()
        if result:
            return json.loads(result[0])
        return {}
    
    def getChats(self, username, target_username):
        chats = self._get_chats(username)
        if chats:
            return {
                'status': 'OK',
                'chats': chats[target_username]
            }
        else:
            return {
                'status': 'ERROR',
                'message': 'NOT_FOUND_CHAT'
            }

    def _update_chats(self, username, chats):
        with self.db.connection:
            self.db.cursor.execute('''
                INSERT INTO user_chats (username, chats)
                VALUES (?, ?)
                ON CONFLICT(username)
                DO UPDATE SET chats = excluded.chats
            ''', (username, json.dumps(chats)))
            self.db.connection.commit()

    def sendMessage(self, from_user, to_user, message, message_id, timestamp=None, reply=None):
        if self.user_manager.username_access(to_user)['status'] == 'OK':
            if timestamp is None:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


            from_chats = self._get_chats(from_user)
            to_chats = self._get_chats(to_user)

            new_message = {
                'from_user': from_user,
                'to_user': to_user,
                'message': message,
                'timestamp': timestamp,
                'message_id': message_id,
                'reply_data': reply
            }

            if to_user not in from_chats:
                from_chats[to_user] = {}
            from_chats[to_user][message_id] = new_message
            self._update_chats(from_user, from_chats)

            if from_user not in to_chats:
                to_chats[from_user] = {}
            to_chats[from_user][message_id] = new_message
            self._update_chats(to_user, to_chats)

            return {'status': 'OK', 'message': new_message}
        else:
            return {'status': 'USER_NOT_FOUND'}

    def initialize_user_messages(self, username):
        pass

    def sendGroupMessage(self, group_name, from_user, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message_id = secrets.token_urlsafe()
        with self.db.connection:
            self.db.cursor.execute('''
                INSERT INTO group_messages (group_name, from_user, message, timestamp, message_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (group_name, from_user, message, timestamp, message_id))
            self.db.connection.commit()
        return {'status': 'OK', 'message': {'group_name': group_name, 'from_user': from_user, 'message': message, 'timestamp': timestamp, 'message_id': message_id}}

    def create_group(self, group_name, profile=None, bio=None):
        default_profile = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRFEZSqk8dJbB0Xc-fr6AWv2aocxDdFpN6maQ&'
        if profile is None or profile.strip() == '':
            profile = default_profile

        try:
            with self.db.connection:
                self.db.cursor.execute('''
                    INSERT INTO groups (group_name, profile, bio)
                    VALUES (?, ?, ?)
                ''', (group_name, profile, bio))
                self.db.connection.commit()
            return {'status': 'OK', 'group': {'group_name': group_name, 'profile': profile, 'bio': bio}}
        except sqlite3.IntegrityError:
            return {'status': 'GROUP_EXISTS'}

    def add_member_to_group(self, group_name, username):
        if self.user_manager.username_access(username)['status'] == 'OK':
            with self.db.connection:
                self.db.cursor.execute('''
                    INSERT OR IGNORE INTO group_members (group_name, username)
                    VALUES (?, ?)
                ''', (group_name, username))
                self.db.connection.commit()
            return {'status': 'OK', 'group_name': group_name, 'username': username}
        else:
            return {'status': 'USER_NOT_FOUND'}

    def remove_member_from_group(self, group_name, username):
        with self.db.connection:
            self.db.cursor.execute('''
                DELETE FROM group_members 
                WHERE group_name = ? AND username = ?
            ''', (group_name, username))
            self.db.connection.commit()
        return {'status': 'OK', 'group_name': group_name, 'username': username}

    def get_group_members(self, group_name):
        self.db.cursor.execute('''
            SELECT username FROM group_members 
            WHERE group_name = ?
        ''', (group_name,))
        members = self.db.cursor.fetchall()
        return {'status': 'OK', 'members': [member[0] for member in members]}

class GroupManager:
    def __init__(self, user_manager):
        self.user_manager = user_manager
        self.db = user_manager.db

    def create_group(self, group_name, profile=None, bio=None):
        default_profile = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRFEZSqk8dJbB0Xc-fr6AWv2aocxDdFpN6maQ&'
        if profile is None or profile.strip() == '':
            profile = default_profile

        try:
            with self.db.connection:
                self.db.cursor.execute('''
                    INSERT INTO groups (group_name, profile, bio)
                    VALUES (?, ?, ?)
                ''', (group_name, profile, bio))
                self.db.connection.commit()
            return {'status': 'OK', 'group': {'group_name': group_name, 'profile': profile, 'bio': bio}}
        except sqlite3.IntegrityError:
            return {'status': 'GROUP_EXISTS'}

    def add_member_to_group(self, group_name, username):
        if self.user_manager.username_access(username)['status'] == 'OK':
            with self.db.connection:
                self.db.cursor.execute('INSERT OR IGNORE INTO group_members (group_name, username) VALUES (?, ?)', (group_name, username))
                self.db.connection.commit()
            return {'status': 'OK', 'group_name': group_name, 'username': username}
        else:
            return {'status': 'USER_NOT_FOUND'}

    def remove_member_from_group(self, group_name, username):
        with self.db.connection:
            self.db.cursor.execute('DELETE FROM group_members WHERE group_name = ? AND username = ?', (group_name, username))
            self.db.connection.commit()
        return {'status': 'OK', 'group_name': group_name, 'username': username}

    def get_group_members(self, group_name):
        self.db.cursor.execute('SELECT username FROM group_members WHERE group_name = ?', (group_name,))
        members = self.db.cursor.fetchall()
        return {'status': 'OK', 'members': [member[0] for member in members]}

    def send_group_message(self, group_name, from_user, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message_id = secrets.token_urlsafe()
        with self.db.connection:
            self.db.cursor.execute('INSERT INTO group_messages (group_name, from_user, message, timestamp, message_id) VALUES (?, ?, ?, ?, ?)',
                                  (group_name, from_user, message, timestamp, message_id))
            self.db.connection.commit()
        return {'status': 'OK', 'message': {'group_name': group_name, 'from_user': from_user, 'message': message, 'timestamp': timestamp, 'message_id': message_id}}

    def get_group_info(self, group_name):
        self.db.cursor.execute('SELECT * FROM groups WHERE group_name = ?', (group_name,))
        group = self.db.cursor.fetchone()
        if group:
            return {'status': 'OK', 'group': {'group_name': group[0], 'profile': group[1], 'bio': group[2]}}
        else:
            return {'status': 'GROUP_NOT_FOUND'}

    def update_group_info(self, group_name, profile=None, bio=None):
        query = 'UPDATE groups SET '
        params = []
        if profile:
            query += 'profile = ?, '
            params.append(profile)
        if bio:
            query += 'bio = ?, '
            params.append(bio)
        query = query.rstrip(', ')
        query += ' WHERE group_name = ?'
        params.append(group_name)
        
        with self.db.connection:
            self.db.cursor.execute(query, params)
            self.db.connection.commit()
        return {'status': 'OK', 'group': {'group_name': group_name, 'profile': profile, 'bio': bio}}

    def delete_group(self, group_name):
        with self.db.connection:
            self.db.cursor.execute('DELETE FROM groups WHERE group_name = ?', (group_name,))
            self.db.cursor.execute('DELETE FROM group_members WHERE group_name = ?', (group_name,))
            self.db.cursor.execute('DELETE FROM group_messages WHERE group_name = ?', (group_name,))
            self.db.connection.commit()
        return {'status': 'OK', 'group_name': group_name}

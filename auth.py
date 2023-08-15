from hashlib import sha256

from env import get_password_dict
from env import get_admin_list

users = get_password_dict()
admins = get_admin_list()


def validate(username, password):
    if type(username) != str or type(password) != str:
        return False
    if username not in users:
        return False
    pw = username + password + 'salt'
    # # https://ipsc.ksp.sk/2012/real/problems/i.html :P
    pwhash = sha256(pw.encode('utf-8')).hexdigest()
    return users[username] == pwhash


def is_valid_user(username):
    if type(username) != str:
        return False
    if username not in users:
        return False
    return True


def is_admin(username):
    if type(username) != str:
        return False
    if username in admins:
        return True
    return False


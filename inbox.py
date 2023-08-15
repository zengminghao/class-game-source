import os
import time
import base64


def add_message(filename, message):
    f = open(filename, "a")
    timestamp = int(time.time())
    message = ' '.join(message.split())
    # message = html_escape(message)
    # we trust admin input
    if len(message) == 0: message = "(blank)"
    message = message.encode("utf-8")
    message = base64.b64encode(message)
    message = message.decode("utf-8")
    print(timestamp, message, file=f)
    f.close()


def send_message(user, message):
    add_message("./chat/{}.txt".format(user), message)


def send_global_message(message):
    add_message("./chat/global-chat.txt", message)


def truncate_message(filename):
    try:
        f = open(filename, "r")
        lines = f.readlines()
        if len(lines) > 500:  # higher threshold
            lines = lines[-500:]
        f.close()
        f = open(filename, "w")
        f.writelines(lines)
        f.close()
    except:
        return


def get_message(filename):
    try:
        f = open(filename, "r")
    except:
        return []
    messages = []
    for line in f.readlines():
        timestamp, message = line.split()
        timestamp = int(timestamp)
        message = message.encode("utf-8")
        message = base64.b64decode(message)
        message = message.decode("utf-8")
        messages.append([timestamp, message])
    messages.reverse()
    if len(messages) >= 500:
        truncate_message(filename)
    return messages


def get_global_inbox():
    return get_message("./chat/global-chat.txt")


def get_inbox(user):
    return get_message("./chat/{}.txt".format(user))


def clear_chat():
    for root, dirs, files in os.walk('./chat'):
        for f in files:
            os.unlink(os.path.join(root, f))


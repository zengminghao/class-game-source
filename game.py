def encode_user(obj):
    return ','.join([str(i) for i in obj])


def decode_user(obj):
    obj = obj.split(',')
    for i in range(1, 8):
        obj[i] = int(obj[i])
    return obj


def default_user(name, x, y):
    return [name, x, y, 3, 1, 2, 0, 0]


def encode_coord(obj):
    return chr(ord('A') + obj[1] - 1) + str(obj[0])


def decode_coord(obj):
    return [int(obj[1:]), ord(obj[0]) - ord('A') + 1]


import time
import random
import constants
from inbox import send_message
from inbox import send_global_message

NAME = 0  # str
X_COORD = 1
Y_COORD = 2
HEALTH_POINT = 3
ACTION_POINT = 4
ACTION_RANGE = 5
VOTE_COUNT = 6
KILL_COUNT = 7


class Game:

    def __init__(self):
        self.phase = "stopped"
        self.wintime = constants.INFINITY
        self.heartpos = []
        self.users = {}
        self.alliances = []

    def readsave(self):
        try:
            f = open("save.txt", "r")
        except:
            print("Save Not Found")
            return

        self.phase = f.readline().strip()
        self.wintime = int(f.readline().strip())
        line = f.readline().strip()
        if line != "none":
            self.heartpos = [decode_coord(i) for i in line.split(',')]
        else:
            self.heartpos = []

        n = int(f.readline().strip())
        for i in range(n):
            user = decode_user(f.readline().strip())
            self.users[user[0]] = user

        n = int(f.readline().strip())
        for i in range(n):
            alliance = list(f.readline().strip().split(','))
            self.alliances.append(alliance)

        f.close()

    def writesave(self, path="save.txt"):
        f = open(path, "w")

        print(self.phase, file=f)
        print(self.wintime, file=f)
        if len(self.heartpos) == 0:
            print('none', file=f)
        else:
            print(','.join([encode_coord(i) for i in self.heartpos]), file=f)

        print(len(self.users), file=f)
        for key, val in self.users.items():
            print(encode_user(val), file=f)

        print(len(self.alliances), file=f)
        for val in self.alliances:
            print(','.join(val), file=f)
        f.close()

    def userlist(self):
        return list(self.users.values())

    def heartlist(self):
        return self.heartpos

    def getuser(self, name):
        if name in self.users:
            return self.users.get(name)
        return None

    def in_game(self, user, alive=False, dead=False, minap=0):
        if user not in self.users:
            return False
        g = self.users.get(user)
        if alive and g[HEALTH_POINT] <= 0:
            return False
        if dead and g[HEALTH_POINT] > 0:
            return False
        if g[ACTION_POINT] < minap:
            return False
        return True

    def distance(self, user1, user2):
        l1 = self.users[user1]
        l2 = self.users[user2]
        dx = abs(l1[X_COORD] - l2[X_COORD])
        dy = abs(l1[Y_COORD] - l2[Y_COORD])
        return max(dx, dy)

    def is_taken(self, x, y):
        for key, val in self.users.items():
            if val[X_COORD] == x and val[Y_COORD] == y:
                return True
        return False

    def set_phase(self, x):
        if self.phase == x:
            return
        self.phase = x
        if x == "running":
            send_global_message("The game has started.")
        elif x == "setup":
            send_global_message("The game is setup.")
        elif x == "stopped":
            send_global_message("The game is stopped.")

    def updateap(self):
        if self.phase != "running":
            return

        if self.wintime < int(time.time()) - constants.DELTA:
            for key, val in self.users.items():
                if [val[X_COORD], val[Y_COORD]] == constants.CENTRE:
                    send_global_message("{} won! Congratulations!".format(key))
                    self.phase = "stopped"
                    self.wintime = int(time.time())
                    return

        maxvote, countvote = 1, 0
        for key, val in self.users.items():
            if val[VOTE_COUNT] > maxvote:
                maxvote = val[VOTE_COUNT]
                countvote = 1
            elif val[VOTE_COUNT] == maxvote:
                countvote += 1

        for key, val in self.users.items():
            val[ACTION_POINT] += 1
            if val[VOTE_COUNT] == maxvote:
                delta = (2 if countvote == 1 else 1)
                val[ACTION_POINT] += delta
                message = "You received {} bonus action point{}.".format(
                    delta, 's' if delta > 1 else '')
                send_message(key, message)
            val[VOTE_COUNT] = 0

        message = "Action points are updated."

        # new heart
        cnt = 0
        while cnt <= 200:
            cnt += 1
            x = random.randint(1, constants.ROW)
            y = random.randint(1, constants.COL)
            if [x, y] in self.heartpos:
                continue
            if self.is_taken(x, y):
                continue
            self.heartpos.append([x, y])
            message += " A new heart is spawned at {}.".format(encode_coord([x, y]))
            break

        send_global_message(message)

    def join(self, user, x, y):
        if self.phase != "setup":
            return "You cannot join the game when it is {}.".format(self.phase), "danger"
        if not (1 <= x <= constants.ROW and 1 <= y <= constants.COL):
            return "Invalid coordinate.", "danger"
        if self.in_game(user):
            return "You are already in the game.", "warning"
        if self.is_taken(x, y) or ([x, y] in self.heartpos):
            return "The square is occupied.", "danger"
        if abs(x - constants.CENTRE_X) <= 2 and abs(y - constants.CENTRE_Y) <= 2:
            return "You cannot join around the centre.", "danger"
        self.users[user] = default_user(user, x, y)
        message = 'You joined at {}.'.format(encode_coord([x, y]))
        send_message(user, message)
        return message, "success"

    def move(self, user, dir):
        if self.phase != "running":
            return "The game is not running.", "danger"
        if not self.in_game(user, alive=True):
            return "You are not alive.", "danger"
        if not self.in_game(user, minap=1):
            return "You do not have enough action points.", "danger"
        dx, dy = 0, 0
        if 'n' in dir: dx = -1
        if 's' in dir: dx = 1
        if 'w' in dir: dy = -1
        if 'e' in dir: dy = 1
        x = int(self.users[user][X_COORD])
        y = int(self.users[user][Y_COORD])
        nx = x + dx
        ny = y + dy
        if not (1 <= nx <= constants.ROW and 1 <= ny <= constants.COL):
            return "You are moving out of the board.", "danger"
        if self.is_taken(nx, ny):
            return "The square is occupied.", "danger"
        self.users[user][ACTION_POINT] -= 1
        self.users[user][X_COORD] = nx
        self.users[user][Y_COORD] = ny
        message = 'You moved to {}.'.format(encode_coord([nx, ny]))
        if [nx, ny] == constants.CENTRE:
            message = 'You moved to the centre of the board. Yay!'
        if [nx, ny] in self.heartpos:
            self.heartpos.remove([nx, ny])
            self.users[user][HEALTH_POINT] += 1
            message += " You also get an extra life."
        send_message(user, message)
        if [nx, ny] == constants.CENTRE:
            send_global_message("{} moved to the centre of the board.".format(user))
            self.wintime = int(time.time())
        if [x, y] == constants.CENTRE:
            send_global_message("{} has left the centre of the board.".format(user))
            self.wintime = constants.INFINITY
        return message, "success"

    def set_alliance(self, user1, user2):
        if user1 not in self.users.keys():
            return "User 1 not in game.", "danger"
        if user2 not in self.users.keys():
            return "User 2 not in game.", "danger"
        #print(self.alliances)
        #print([user1, user2])
        if [user1, user2] in self.alliances or [user2, user1] in self.alliances:
            while [user1, user2] in self.alliances:
                self.alliances.remove([user1, user2])
            while [user2, user1] in self.alliances:
                self.alliances.remove([user2, user1])
            return "You removed ally for {} and {}.".format(user1, user2), "info"
        else:
            self.alliances.append([user1, user2])
            self.alliances.append([user2, user1])
            return "You added ally for {} and {}.".format(user1, user2), "success"

    def get_alliance(self, user):
        result = []
        for alliance in self.alliances:
            for member in alliance:
                if user in alliance and member != user and member not in result:
                    result.append(member)
        result.sort()
        if len(result) == 0:
            return ""
        if len(result) == 1:
            return "Your ally is " + result[0] + "."
        if len(result) == 2:
            return "Your allies are " + result[0] + " and " + result[1] + "."
        return "Your allies are " + (', '.join(result[:-1]) + ' and ' + result[-1]) + "."

    def check_death(self, user, target):
        deadlist = [target]
        cur = 0
        while cur < len(deadlist):
            dead = deadlist[cur]

            dead_message = "You are killed for failing to protect your ally(s)."
            if self.users[dead][ACTION_POINT] > 0:
                dead_message += " Your action points are lost."

            if [self.users[dead][X_COORD], self.users[dead][Y_COORD]] == constants.CENTRE:
                self.wintime = constants.INFINITY
            self.users[dead][X_COORD] = 0
            self.users[dead][Y_COORD] = 0
            self.users[dead][HEALTH_POINT] = 0
            self.users[dead][ACTION_POINT] = 0

            if dead == target:
                send_global_message("{} killed {}.".format(user, dead))
            else:
                send_global_message(
                    "{} is killed for failing to protect their ally(s).".format(dead))
                send_message(dead, dead_message)

            for key, val in self.users.items():
                if [dead, key] in self.alliances or [key, dead] in self.alliances:
                    if val[HEALTH_POINT] > 0 and key not in deadlist:
                        deadlist.append(key)

            cur += 1

        self.users[user][KILL_COUNT] += len(deadlist)

    def attack(self, user, target):
        if self.phase != "running":
            return "The game is not running.", "danger"
        if not self.in_game(user, alive=True):
            return "You are not alive.", "danger"
        if not self.in_game(target, alive=True):
            return "The target is not alive.", "danger"
        if not self.in_game(user, minap=1):
            return "You do not have enough action points.", "danger"
        if self.distance(user, target) > self.users[user][ACTION_RANGE]:
            return "The target is out of range.", "danger"
        message_user = "You attacked {}.".format(target)
        message_target = "{} attacked you.".format(user)
        self.users[user][ACTION_POINT] -= 1
        self.users[target][HEALTH_POINT] -= 1
        if self.users[target][HEALTH_POINT] <= 0:
            # you take away their action points
            gainAP = max(self.users[target][ACTION_POINT], 0)
            self.users[user][ACTION_POINT] += gainAP
            self.users[target][ACTION_POINT] -= gainAP
            message_user = "You killed {}.".format(target)
            message_target = "{} killed you.".format(user)
            if gainAP > 0:
                message_user += " You stealed {} action point{}.".format(
                    gainAP, "s" if gainAP > 1 else "")
                message_target += " Your action points are stolen."
            self.check_death(user, target)
        send_message(user, message_user)
        send_message(target, message_target)
        return message_user, "success"

    def trade(self, user, target):
        if self.phase != "running":
            return "The game is not running.", "danger"
        if not self.in_game(user, alive=True):
            return "You are not alive.", "danger"
        if not self.in_game(target, alive=True):
            return "The target is not alive.", "danger"
        if not self.in_game(user, minap=1):
            return "You do not have enough action points.", "danger"
        if self.distance(user, target) > self.users[user][ACTION_RANGE]:
            return "The target is out of range.", "danger"
        self.users[user][ACTION_POINT] -= 1
        self.users[target][ACTION_POINT] += 1
        message_user = "You gave {} one action point.".format(target)
        message_target = "You received one action point from {}.".format(user)
        send_message(user, message_user)
        send_message(target, message_target)
        return message_user, "success"

    def upgrade(self, user):
        if self.phase != "running":
            return "The game is not running.", "danger"
        if not self.in_game(user, alive=True):
            return "You are not alive.", "danger"
        if not self.in_game(user, minap=3):
            return "You do not have enough action points.", "danger"
        self.users[user][ACTION_POINT] -= 3
        self.users[user][ACTION_RANGE] += 1
        message_user = "You upgraded your tank."
        send_message(user, message_user)
        return message_user, "success"

    def heal(self, user):
        if self.phase != "running":
            return "The game is not running.", "danger"
        if not self.in_game(user, alive=True):
            return "You are not alive.", "danger"
        if not self.in_game(user, minap=2):
            return "You do not have enough action points.", "danger"
        self.users[user][ACTION_POINT] -= 2
        self.users[user][HEALTH_POINT] += 1
        message_user = "You healed your tank."
        send_message(user, message_user)
        return message_user, "success"

    def vote(self, user, target):
        if self.phase != "running":
            return "The game is not running.", "danger"
        if not self.in_game(user, dead=True):
            return "You are not dead.", "danger"
        if not self.in_game(target, alive=True):
            return "The target is not alive.", "danger"
        if not self.in_game(user, minap=1):
            return "You do not have enough action points.", "danger"
        self.users[user][ACTION_POINT] -= 1
        self.users[target][VOTE_COUNT] += 1
        message_user = "You voted {}.".format(target)
        send_message(user, message_user)
        return message_user, "success"


from game import Game
from game import encode_coord
import constants
import common

# constants

NAME = 0  # str
X_COORD = 1
Y_COORD = 2
HEALTH_POINT = 3
ACTION_POINT = 4
ACTION_RANGE = 5
VOTE_COUNT = 6
KILL_COUNT = 7

# Aliases

from env import get_names_dict

NAMES = get_names_dict()

# Profile Pictures

from env import get_profiles_dict

PROFILES = get_profiles_dict()


def get_profile(user):
    if user in PROFILES:
        return PROFILES.get(user)
    return 'https://cdn.discordapp.com/embed/avatars/{}.png'.format(abs(hash(user)) % 5)


# PAGE: status


def get_backend_status(user):
    x = Game()
    x.readsave()
    info = x.getuser(user)
    if info is not None:
        info = [info[HEALTH_POINT], info[ACTION_POINT], info[ACTION_RANGE]]
        info += [x.get_alliance(user)]
    else:
        info = []
    info += [x.wintime, x.phase]
    return info


def backend_status(user):
    content = ""
    obj = get_backend_status(user)
    if len(obj) == 2:
        wt, phase = obj
        content = "The game is {}.\n".format(phase)
        if phase == "running":
            content += common.next_7am() + "\n"
        content += "\n"

        content += "You are not in the game.\n"
    else:
        hp, ap, ar, al, wt, phase = obj
        content = "The game is {}.\n".format(phase)
        if phase == "running":
            content += common.next_7am() + "\n"
        content += "\n"

        if hp > 0:
            content += "Action Points: " + str(ap) + ".\n"
            content += " Action Range: " + str(ar) + ".\n"
            content += "        Lives: " + str(hp) + ".\n"
            content += str(al) + "\n"
        else:
            content += "You are dead. :(\n"
            content += "Action Points: " + str(ap) + ".\n"

    content = content.replace('\n', '<br>')
    return content


from inbox import get_global_inbox, get_inbox


def backend_global_inbox():
    messages = get_global_inbox()
    messages = ["[{}] {}".format(common.pretty_date(t), m) for t, m in messages]
    content = '<br>'.join(messages)
    if len(content) == 0: content = "Nothing here to see!"
    return content


def backend_inbox(user):
    messages = get_inbox(user)
    messages = ["[{}] {}".format(common.pretty_date(t), m) for t, m in messages]
    content = '<br>'.join(messages)
    if len(content) == 0: content = "Nothing here to see!"
    return content


# PAGE: board + users


def get_backend_users(username):
    x = Game()
    x.readsave()

    userlist = []
    for user in x.userlist():
        info = [user[NAME], user[X_COORD], user[Y_COORD], user[HEALTH_POINT], user[KILL_COUNT]]
        userlist.append(info)
    userlist = sorted(userlist, key=lambda item: (item[0] != username, item[0].upper()))

    heartlist = x.heartlist()

    info = x.getuser(username)
    if info is not None:
        info = [info[HEALTH_POINT], info[ACTION_POINT], info[ACTION_RANGE]]

    return userlist, heartlist, x.phase, info


def backend_users(user, url_prefix):
    userlist, heartlist, phase, g = get_backend_users(user)

    is_alive = False
    curx, cury = -1, -1
    for uname, coordx, coordy, hp, kc in userlist:
        if user == uname and hp > 0:
            is_alive = True
            curx, cury = coordx, coordy

    content = 'You are not in the game.<br>'
    if g is not None:
        content = 'You have {} action point{}.<br>'.format(g[1], "" if g[1] == 1 else "s")

    if len(userlist) > 0:
        content += '<div class="table-responsive" style="border: 0;">'
        content += '<table id="myTable"><thead><tr>'
        content += '<th style="width:12ch;">User<span class="sortable-th"></span></th>'
        content += '<th>Pos<span class="sortable-th"></span></th>'
        content += '<th>Lives<span class="sortable-th"></span></th>'
        if g is not None:
            if is_alive:
                content += '<th>Actions</th>'
            else:
                content += '<th>Action</th>'
        content += '<th>Kills<span class="sortable-th"></span></th>'
        content += '</tr></thead><tbody>'
    else:
        content += "The board is empty."

    for uname, coordx, coordy, hp, kc in userlist:
        content += '<tr>\n'

        # User
        medal = ''
        if [coordx, coordy] == constants.CENTRE:
            medal = '👑'

        alias = NAMES[uname] if (uname in NAMES) else uname
        content += '<td><span class="name">{}</span>'.format(uname)
        content += '<span class="alias" style="display: none;">{}</span>'.format(alias)
        content += '{}</td>\n'.format(medal)

        # Position
        dist = 12
        score = 0
        if hp > 0:
            dist = max(abs(coordx - constants.CENTRE_X), abs(coordy - constants.CENTRE_Y))
            score = [12, 9, 7, 5, 4, 3, 2, 1][max(0, min(7, dist))]
        sty = 'color:{}'.format(constants.COLORS[score])
        content += '<td style="{}" distance="{}">{}</td>\n'.format(
            sty, dist,
            encode_coord([coordx, coordy]) if hp > 0 else '-')

        # Health
        score = [0, 3, 5, 8, 11, 12][max(0, min(5, hp))]
        sty = 'color:{}'.format(constants.COLORS[score])
        content += '<td style="{}">{}</td>\n'.format(sty, hp if hp > 0 else '-')

        # Actions
        if g is not None:
            action1, action2 = 'attack', 'trade'
            ap1, ap2 = 1, 1
            if user == uname:
                action1, action2 = 'upgrade', 'heal'
                ap1, ap2 = 3, 2
            if not is_alive:
                action1, action2 = 'vote', 'haunt'

            sty1, sty2 = '', ''
            if g[1] < ap1: sty1 = 'class="disabled"'
            if g[1] < ap2: sty2 = 'class="disabled"'
            dist = max(abs(curx - coordx), abs(cury - coordy))
            if hp <= 0 or (action1 == 'attack' and dist > g[2]):
                sty1 = 'class="disabled"'
                sty2 = 'class="disabled"'

            if is_alive:
                content += '<td><span style="width:7ch;">'
                content += '<a href="{}" onclick="disableLinks();" {}>{}</a> '.format(
                    url_prefix + "?actionid=" + action1 + "&userid=" + uname, sty1,
                    action1.capitalize())
                content += '</span><span style="width:7ch;">'
                content += '<a href="{}" onclick="disableLinks();" {}>{}</a>'.format(
                    url_prefix + "?actionid=" + action2 + "&userid=" + uname, sty2,
                    action2.capitalize())
                content += '</span></td>'
            else:
                content += '<td><a href="{}" onclick="disableLinks();" {}>{}</a></td>'.format(
                    url_prefix + "?actionid=" + action1 + "&userid=" + uname, sty1,
                    action1.capitalize())

        # Kill
        score = [12, 5, 3, 2, 1, 0][max(0, min(5, kc))]
        sty = 'color:{}'.format(constants.COLORS[score])
        content += '<td style="{}">{}</td>\n'.format(sty, kc if kc > 0 else '')

        content += '</tr>\n'

    if len(userlist) > 0:
        content += '</tbody></table></div>'
        content += '<br>'
        content += '<button id="aliastoggle" class="btn btn-default">show names</button>'

    return content


def backend_board(user, url_prefix):
    userlist, heartlist, phase, g = get_backend_users(user)

    curx, cury = -1, -1
    for uname, x, y, hp, kc in userlist:
        if user == uname and hp > 0:
            curx, cury = x, y

    texts = [[None for j in range(constants.COL + 2)] for i in range(constants.ROW + 2)]
    images = [[None for j in range(constants.COL + 2)] for i in range(constants.ROW + 2)]
    links = [[None for j in range(constants.COL + 2)] for i in range(constants.ROW + 2)]
    styles = [["lightblue" for j in range(constants.COL + 2)] for i in range(constants.ROW + 2)]
    scripts = [[None for j in range(constants.COL + 2)] for i in range(constants.ROW + 2)]

    # chessboard
    for i in range(1, constants.ROW + 1):
        for j in range(1, constants.COL + 1):
            if (i + j) % 2 == 1:
                styles[i][j] = "#A0D0E0"

    # move options
    if user is None:
        pass
    elif g is None and phase == "setup":  # not in game, join
        for i in range(1, constants.ROW + 1):
            for j in range(1, constants.COL + 1):
                if abs(i - constants.CENTRE_X) <= 2 and abs(j - constants.CENTRE_Y) <= 2:
                    pass
                else:
                    texts[i][j] = "Go"
                    links[i][j] = "{}?dir=join&x={}&y={}".format(url_prefix, i, j)
    elif g is not None and g[0] > 0:  # alive, move
        for i in range(1, constants.ROW + 1):
            for j in range(1, constants.COL + 1):
                if phase == "running" and abs(i - curx) <= 1 and abs(j - cury) <= 1 and (
                        i != curx or j != cury):
                    dir = ''
                    if i < curx: dir += 'n'
                    if i > curx: dir += 's'
                    if j < cury: dir += 'w'
                    if j > cury: dir += 'e'
                    texts[i][j] = "Go"
                    links[i][j] = "{}?dir={}".format(url_prefix, dir)
                if abs(i - curx) <= g[2] and abs(j - cury) <= g[2]:
                    if (i + j) % 2 == 1:
                        styles[i][j] = "#70a060"
                    else:
                        styles[i][j] = "#74a662"

    styles[constants.CENTRE_X][constants.CENTRE_Y] = "Gold"

    # heartlist
    for x, y in heartlist:
        if texts[x][y] == "Go":
            texts[x][y] = "heart-go"
            images[x][y] = get_profile('heart-go')
        else:
            texts[x][y] = "heart"
            images[x][y] = get_profile('heart-image')

    # user profile pictures
    for uname, x, y, hp, kc in userlist:
        if 1 <= x <= constants.ROW and 1 <= y <= constants.COL and hp > 0:
            alias = (' (' + NAMES[uname] + ')') if (uname in NAMES) else ''
            texts[x][y] = uname + alias
            images[x][y] = get_profile(uname)
            links[x][y] = None

            params = "0,0,0"
            if g is not None:
                if g[0] <= 0:
                    params = "0,0,1"
                elif user == uname:
                    params = "0,1,0"
                else:
                    params = "1,0,0"
            params += "," + str(hp)
            scripts[x][y] = "setuid('{}','{}','{}',{})".format(uname, alias, images[x][y], params)
            print(scripts[x][y])

    # coordinates
    for i in range(1, constants.ROW + 1):
        texts[i][0] = str(i)
        texts[i][constants.COL + 1] = str(i)

    for j in range(1, constants.COL + 1):
        texts[0][j] = chr(ord('A') + j - 1)
        texts[constants.ROW + 1][j] = chr(ord('A') + j - 1)

    content = '<table cellpadding="0" cellspacing="0">'
    for i in range(constants.ROW + 2):
        content += '<tr>'
        for j in range(constants.COL + 2):
            sty = ''
            if styles[i][j] is not None:
                sty = 'style="background-color:{}"'.format(styles[i][j])

            content += '<td {}>'.format(sty)

            if links[i][j] is not None:
                content += '<a href="{}" onclick="disableLinks();">'.format(links[i][j])

            if images[i][j] is not None:
                content += '<img src="{}" title="{}" '.format(images[i][j], texts[i][j])
                if scripts[i][j] is not None:
                    content += ' onclick="{}" '.format(scripts[i][j])
                content += '{}>'.format(' class="epic"' if styles[i][j] == 'Gold' else '')
            else:
                if texts[i][j] is not None:
                    content += texts[i][j]

            if links[i][j] is not None:
                content += '</a>'

            content += '</td>'

        content += '</tr>'
    content += '</table>\n'

    return content


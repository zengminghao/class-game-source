from auth import validate
from auth import is_valid_user
from auth import is_admin

from flask import Flask
from flask import request, url_for, redirect, flash, session
from flask import make_response, render_template

from env import get_secret_key

app = Flask(__name__, template_folder='template')
app.secret_key = bytes(get_secret_key(), 'ascii')


@app.before_first_request
def init_app():
    session.permanent = True


# error handler


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html")


# login & logout


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'GET':
        resp = make_response(render_template('login.html'))
        return resp

    if request.method == 'POST':
        user = request.form.get('user')
        password = request.form.get('pass')

        if not validate(user, password):
            flash("Invalid username or password", 'danger')
            return redirect(url_for('login'))

        session["user"] = user

        flash("You have successfully logged in!", 'success')
        return redirect(url_for('home'))

    return make_response('Unknown Method', 405)


@app.route('/logout', methods=["GET"])
def logout():
    session["user"] = None
    flash("You have logged out", 'info')
    return redirect(url_for('login'))


# redirect


def redirect_login(anonymous=False, admin=False):
    if not session.get("user"):
        if anonymous:
            return None

        flash("Please login to access the game.", 'warning')
        resp = redirect(url_for('login'))
        return resp

    user = session["user"]

    if admin and (not is_admin(user)):
        flash("You are not admin.", "danger")
        return redirect_back()

    return None


def redirect_back():
    return redirect(request.referrer or url_for('home'))


# admins

from game import Game
from inbox import send_global_message
from inbox import clear_chat

# message


@app.route('/admin', methods=["GET", "POST"])
def admin():
    page = redirect_login(admin=True)
    if page is not None:
        return page
    user = session['user'] if session.get('user') else None

    if request.method == 'GET':
        temp = render_template('admin.html', username=user, logged_in=True)
        return make_response(temp)

    if request.method != 'POST':
        return make_response('Unknown Method', 405)

    actionid = request.form.get('actionid')

    if actionid == "message":
        message = request.form.get('response')
        send_global_message(message)
        flash('You added an announcement.', 'success')
        return redirect(url_for('admin'))
    elif actionid == "status":
        phase = request.form.get('phase')
        if phase not in ["stopped", "setup", "running"]:
            flash("Invalid phase.", "danger")
            return redirect_back()
        g = Game()
        g.readsave()
        g.set_phase(phase)
        g.writesave()
        flash("Status updated to {}!".format(phase), "success")
    elif actionid == "reset":
        g = Game()
        g.writesave()
        send_global_message("The game is reset.")
        flash("The game is reset.", "success")
    elif actionid == "update":
        g = Game()
        g.readsave()
        g.updateap()
        g.writesave()
        flash("The action points are updated.", "success")
    elif actionid == "clear":
        clear_chat()
        flash("You cleared the chats.", "info")
    elif actionid == "error":
        print(0 / 0)
        flash("You made an error!", "info")
    elif actionid == "ally":
        g = Game()
        g.readsave()
        user1 = request.form.get('user1')
        user2 = request.form.get('user2')
        message, verdict = g.set_alliance(user1, user2)
        g.writesave()
        flash(message, verdict)
    else:
        flash("Welcome, admin!", "info")

    return redirect_back()


# actions


@app.route('/action', methods=["GET"])
def action():
    page = redirect_login()
    if page is not None:
        return page
    user = session['user'] if session.get('user') else None

    actionid = request.args.get('actionid')
    userid = request.args.get('userid')

    if actionid in ['attack', 'trade']:
        if user == userid:
            flash('You cannot {} yourself.'.format(actionid), 'danger')
            return redirect_back()
    elif actionid in ['upgrade', 'heal']:
        if user != userid:
            flash('You cannot {} others.'.format(actionid), 'danger')
            return redirect_back()
    elif actionid in ['vote']:
        pass
    else:
        flash('Invalid action', 'danger')
        return redirect_back()

    if not is_valid_user(userid):
        flash('Invalid user', 'danger')
        return redirect_back()

    message, verdict = "Nothing happened.", "info"
    g = Game()
    g.readsave()

    if actionid == 'attack':
        message, verdict = g.attack(user, userid)
    if actionid == 'trade':
        message, verdict = g.trade(user, userid)
    if actionid == 'upgrade':
        message, verdict = g.upgrade(user)
    if actionid == 'heal':
        message, verdict = g.heal(user)
    if actionid == 'vote':
        message, verdict = g.vote(user, userid)

    g.writesave()
    flash(message, verdict)
    return redirect_back()


@app.route('/move', methods=["GET"])
def move():
    page = redirect_login()
    if page is not None:
        return page
    user = session['user'] if session.get('user') else None

    dir = request.args.get('dir')
    if dir not in ['n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw', 'join']:
        flash('Invalid direction', 'danger')
        return redirect_back()

    x, y = -1, -1
    if dir == 'join':
        try:
            x = int(request.args.get('x'))
            y = int(request.args.get('y'))
        except:
            flash('Invalid parameters', 'danger')
            return redirect_back()

    message, verdict = "Nothing happened.", "info"
    g = Game()
    g.readsave()

    if dir == 'join':
        message, verdict = g.join(user, x, y)
    else:
        message, verdict = g.move(user, dir)

    g.writesave()
    flash(message, verdict)
    return redirect_back()


# pages

from pastel import backend_status
from pastel import backend_inbox, backend_global_inbox
from pastel import backend_users
from pastel import backend_board


@app.route('/', methods=["GET"])
def home():
    page = redirect_login(anonymous=True)
    if page is not None:
        return page
    user = session['user'] if session.get('user') else None

    logged_in = user is not None
    if user is None: user = 'anonymous user'
    temp = render_template('home.html',
                           username=user,
                           logged_in=logged_in,
                           show_hidden=is_admin(user))
    return make_response(temp)


@app.route('/rules', methods=["GET"])
def rules():
    user = session['user'] if session.get('user') else None

    logged_in = user is not None
    temp = render_template('rules.html', logged_in=logged_in, show_hidden=is_admin(user))
    return make_response(temp)


@app.route('/status', methods=["GET"])
def status():
    page = redirect_login()
    if page is not None:
        return page
    user = session['user'] if session.get('user') else None

    if user is None:
        user = 'anonymous user'
        content = 'You are not logged in.'
        inbox = 'You are not logged in.'
        logged_in = False
    else:
        content = backend_status(user)
        inbox = backend_inbox(user)
        logged_in = True

    global_inbox = backend_global_inbox()
    temp = render_template('status.html',
                           username=user,
                           logged_in=logged_in,
                           show_hidden=is_admin(user),
                           content=content,
                           inbox=inbox,
                           global_inbox=global_inbox)
    return make_response(temp)


@app.route('/users', methods=["GET"])
def users():
    page = redirect_login(anonymous=True)
    if page is not None:
        return page
    user = session['user'] if session.get('user') else None

    content = backend_users(user, url_for('action'))
    logged_in = user is not None
    if user is None:
        user = 'anonymous user'
    temp = render_template('users.html',
                           username=user,
                           logged_in=logged_in,
                           show_hidden=is_admin(user),
                           content=content)
    return make_response(temp)


@app.route('/board', methods=["GET"])
def board():
    page = redirect_login(anonymous=True)
    if page is not None:
        return page
    user = session['user'] if session.get('user') else None

    content = backend_board(user, url_for('move'))
    logged_in = user is not None
    if user is None: user = 'anonymous user'
    temp = render_template('board.html',
                           username=user,
                           logged_in=logged_in,
                           show_hidden=is_admin(user),
                           content=content)
    return make_response(temp)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=0)


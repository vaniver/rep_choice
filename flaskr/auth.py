import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        display_name = request.form['display_name']
        db = get_db()
        error = None

        if not display_name:
            error = 'display name is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (display_name, bio, contact_down, contact_up, last_choice_added, tier, has_ever_tier, voice) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (display_name, "", "", "", 0, 0, 0, 1),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {display_name} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE id = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
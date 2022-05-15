import datetime

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from flaskr.auth import login_required
from flaskr.db import get_db

from flaskr.rep_assignment import allocate_reps, local_update_reps

bp = Blueprint('users', __name__)

@bp.route('/')
def index():
    db = get_db()
    user_list = db.execute(
        'SELECT id, display_name, bio, voice'
        ' FROM user'
        ' ORDER BY voice DESC'
        ' LIMIT 200'
    ).fetchall()
    return render_template('users/index.html', user_list=user_list)

@bp.route('/update', methods=('GET', 'POST'))
@login_required
def update():
    curr_desc = get_db().execute(
        'SELECT * FROM user WHERE id = ?', (g.user['id'], )
    ).fetchone()
    if request.method == 'POST':
        display_name = request.form['display_name']
        bio = request.form['bio']
        contact_down = request.form['contact_down']
        contact_up = request.form['contact_up']

        error = None

        if not display_name:
            error = 'Display name is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE user SET display_name = ?, bio = ?, contact_down = ?, contact_up = ?'
                ' WHERE id = ?',
                (display_name, bio, contact_down, contact_up, g.user['id'])
            )
            db.commit()
            return redirect(url_for('users.index'))

    return render_template('users/update.html', curr_desc=curr_desc)

@bp.route('/choose', methods=('GET', 'POST'))
@login_required
def choose():
    db = get_db()
    curr_choice = db.execute(
        'SELECT * FROM choice WHERE down_id = ?', (g.user['id'],)
    ).fetchone()
    prev_choice = curr_choice != None
    if request.method == 'POST':
        up1 = request.form['up1']
        up2 = request.form['up2']
        up3 = request.form['up3']
        error = None

        if not up1:
            error = 'You have to have a first choice.'

        if (up1 == up2 and up1 != "" and up2 != "") or (up1 == up3 and up1 != "" and up2 != "") or (up2 == up3 and up2 != "" and up3 != ""):
            error = f"You have to have unique choices. {up1}, {up2}, {up3}"

        try:
            up1 = int(up1)
        except:
            buf = f"\n{up1} should be an integer.\n"
            error = error + buf if error else buf
        try:
            up2 = int(up2)
        except:
            buf = f"\n{up2} should be an integer.\n"
            error = error + buf if error else buf
        try:
            up3 = int(up3)
        except:
            buf = f"\n{up3} should be an integer.\n"
            error = error + buf if error else buf

        if g.user['id'] in [up1, up2, up3]:
            error = 'You cannot choose yourself.'

        if error is not None:
            flash(error)
        else:
            if prev_choice:
                db.execute(
                    'UPDATE choice SET up_id_1 = ?, up_id_2 = ?, up_id_3 = ?, time_chosen = ?'
                    ' WHERE down_id = ?',
                    (up1, up2, up3, datetime.datetime.now(), g.user['id'])
                )
            else:
                db.execute(
                    'INSERT INTO choice (down_id, up_id_1, up_id_2, up_id_3, time_chosen)'
                    ' VALUES (?, ?, ?, ?, ?)',
                    (g.user['id'], up1, up2, up3, datetime.datetime.now())
                )
            db.commit()
            local_update_reps(g.user['id'], )
            return redirect(url_for('users.index'))

    return render_template('users/choose.html', curr_choice=curr_choice)

@bp.route('/links')
@login_required
def links():
    db = get_db()
    curr_tier = db.execute(
        'SELECT tier FROM user WHERE id = ?', (g.user['id'],)
    ).fetchone()
    curr_rep = db.execute(
        'SELECT u.display_name, u.voice, u.contact_down, u.bio FROM user u JOIN reps r ON u.id = r.up_id WHERE r.down_id = ?', (g.user['id'],)
    ).fetchone()
    if curr_tier['tier'] > 0:
        rep_list = db.execute(
            'SELECT down_id FROM reps WHERE up_id = ?', (g.user['id'],)
        ).fetchall()
    else:
        rep_list = []
    return render_template('users/links.html', curr_rep=curr_rep, rep_list=rep_list)


@bp.route('/allocation', methods=('GET', 'POST'))
@login_required
def reallocate():
    db = get_db()
    authorized = False
    curr_tier = db.execute(
        'SELECT tier FROM user WHERE id = ?', (g.user['id'],)
    ).fetchone()
    if curr_tier['tier'] > 1 or g.user['id'] == 1:
        authorized = True
    last_time = db.execute(
        'SELECT start_time, end_time FROM rep_calculations ORDER BY start_time DESC LIMIT 1'
    ).fetchone()
    if last_time is None:
        last_time = datetime.datetime(2000, 1, 1)
        time_took = 0
    else:
        time_took = (datetime.datetime.fromisoformat(last_time['end_time'])- datetime.datetime.fromisoformat(last_time['start_time'])).total_seconds()
        last_time = last_time['start_time']
    num_choices = db.execute(
        'SELECT COUNT(*) FROM choice WHERE time_chosen > ?', (last_time, )
    ).fetchone()['COUNT(*)']
    if request.method == 'POST' and authorized and request.form['allocate'] == 'allocate':
        allocate_reps()
    if authorized:
        return render_template('users/authorized_allocation.html', authorized=authorized, last_time=last_time, time_took=time_took, num_choices=num_choices)
    else:
        return render_template('users/unauthorized_allocation.html', authorized=authorized, last_time=last_time, time_took=time_took, num_choices=num_choices)

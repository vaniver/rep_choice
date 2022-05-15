import datetime

from flaskr.db import get_db

def default_voice_function(voice, tier):
    """A piecewise linear function for voice.
    """
    voice_cutoff = 200 ** (tier + 1)
    if voice < voice_cutoff:
        return voice
    else:
        return voice // 2 + voice_cutoff // 2

def allocate_reps(requester_id = 0, voice_function = default_voice_function, voice_tier_mins= {0: 50, 1: 50*50, 2: 50*50*50,}, top_tier_max=0, tier_max=3):
    """This function is for allocating reps to users when none have been allocated yet.
    IT WILL DELETE reps AND SET ALL TIERS TO 0 AND ALL VOICE TO 1 (before recalculating).
    For partial allocations after a local change, see local_update_reps().

    The algorithm goes as follows:
    1. For each tier i user, point their voice towards their first choice.
    2. For all reps with >=domain_min voice, lock in those rep choices and set them to be tier i+1.
    3. For all reps with <domain_min voice, undo those rep choices reallocate the voice to the user's next highest choice. If any reallocation happens, return to step 2.
    4. Now all tier-i reps have been locked in. Increment i and return to step 1 if the number of tier-i reps is > top_tier_max unless tier > tier_max.

    Note that voice_function should return an int.
    """
    start_time = datetime.datetime.now()
    db = get_db()
    db.execute('DELETE FROM reps;')
    db.execute('UPDATE user SET tier = 0, voice = 1;')
    db.commit()
    tier = 0
    num_at_tier = db.execute('SELECT COUNT(*) FROM user WHERE tier = ?', (tier,)).fetchone()['COUNT(*)']
    real_voice = {}
    while num_at_tier > top_tier_max and tier < tier_max:
        temp_reps = {}
        temp_voice = {}
        prefs = {}
        choices = db.execute('SELECT c.down_id, c.up_id_1, c.up_id_2, c.up_id_3 FROM choice c JOIN user u ON c.down_id = u.id WHERE u.tier = ?', (tier,)).fetchall()
        # Parse all of the choices.
        for choice in choices:
            prefs[choice['down_id']] = [choice['up_id_1']]
            if choice['up_id_2']:
                prefs[choice['down_id']].append(choice['up_id_2'])
            if choice['up_id_3']:
                prefs[choice['down_id']].append(choice['up_id_3'])
        # Assign all of the first preferences.
        for user in prefs.keys():
            if len(prefs[user]) == 0:
                continue
            up_id = prefs[user].pop()
            if up_id in temp_reps:
                temp_reps[up_id].add(user)
                temp_voice[up_id] += real_voice.get(user, 1)
            else:
                temp_reps[up_id] = {user}
                temp_voice[up_id] = real_voice.get(user, 1)
        # Reassign the votes from anyone who didn't clear the bar, least popular first.
        least_voice = min(temp_voice.values()) if len(temp_voice) > 0 else voice_tier_mins[tier]
        while least_voice < voice_tier_mins[tier]:
            least_popular_rep = [up_id for up_id, voice in temp_voice.items() if voice == least_voice][0]
            users_to_reassign = temp_reps[least_popular_rep]
            del temp_reps[least_popular_rep]
            del temp_voice[least_popular_rep]
            for user in users_to_reassign:
                if len(prefs[user]) == 0:
                    continue
                up_id = prefs[user].pop()
                if up_id:
                    if up_id in temp_reps:
                        temp_reps[up_id].add(user)
                        temp_voice[up_id] += real_voice.get(user, 1)
                    else:
                        temp_reps[up_id] = {user}
                        temp_voice[up_id] = real_voice.get(user, 1)
            least_voice = min(temp_voice.values()) if len(temp_voice) > 0 else voice_tier_mins[tier]
        for user, voice in temp_voice.items():
            real_voice[user] = voice_function(voice, tier)
        for up_id, down_ids in temp_reps.items():
            db.execute('INSERT INTO reps (down_id, up_id) VALUES ' + ', '.join([f"({str(down_id)}, {str(up_id)})" for down_id in down_ids]), ())
            db.execute('UPDATE user SET tier = ?, voice = ? WHERE id = ?', (tier+1, real_voice[up_id], up_id))
        db.commit()
        tier += 1
        num_at_tier = db.execute('SELECT COUNT(*) FROM user WHERE tier = ?', (tier,)).fetchone()['COUNT(*)']
    end_time = datetime.datetime.now()
    db.execute('INSERT INTO rep_calculations (requester_id, start_time, end_time) VALUES (?, ?, ?)', (requester_id, start_time, end_time))
    db.commit()

def local_update_reps(userid, prefs, voice_function = default_voice_function):
    """This function is for updating reps after a single user changes their preferences. It will not create or delete any reps, or adjust the rep's voice."""
    db = get_db()
    # Get the user's current tier and voice.
    user = db.execute('SELECT tier, voice FROM user WHERE id = ?', (userid,)).fetchone()
    # Get the tiers of the user's prefs.
    up_id = None
    for pref in prefs:
        if pref:
            up_user = db.execute('SELECT tier FROM user WHERE tier = ? and id = ?', (user['tier'] + 1, userid,)).fetchone()
            if up_user:
                up_id = pref
                break
    if up_id:
        db.execute('DELETE FROM reps WHERE down_id = ?;', (userid,))
        db.execute('INSERT INTO reps (down_id, up_id) VALUES (?, ?)', (userid, up_id))
        db.commit()
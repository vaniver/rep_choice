INSERT INTO user (id, display_name, bio, contact_down, contact_up, last_choice_added, tier, has_ever_tier, voice)
 VALUES (1, 'Alice', 'Test User Bio', 'Test User Contact Down', 'Test User Contact Up', '2016-01-01 00:00:00', 0, 0, 1),
 (2, 'Bob', 'Test User Bio', 'Test User Contact Down', 'Test User Contact Up', '2016-01-01 00:00:00', 0, 0, 1),
 (3, 'Carol', 'Test User Bio', 'Test User Contact Down', 'Test User Contact Up', '2016-01-01 00:00:00', 0, 1, 1),
 (4, 'Dan', 'Test User Bio', 'Test User Contact Down', 'Test User Contact Up', '2016-01-01 00:00:00', 1, 1, 4);

INSERT INTO choice (down_id, up_id_1, up_id_2, up_id_3, time_chosen)
    VALUES (1, 4, 2, 3, '2016-01-01 00:00:00'),
    (2, 4, 3, 1, '2016-01-01 00:00:00'),
    (3, 4, 2, 1, '2016-01-01 00:00:00');

INSERT INTO reps (down_id, up_id)
    VALUES (1, 4),
    (2, 4),
    (3, 4);
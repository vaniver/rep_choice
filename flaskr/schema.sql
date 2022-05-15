DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS choice;
DROP TABLE IF EXISTS reps;
DROP TABLE IF EXISTS rep_calculations;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name VARCHAR(50) NOT NULL,
    bio VARCHAR(280) NOT NULL,
    contact_down VARCHAR(280) NOT NULL,
    contact_up VARCHAR(280) NOT NULL,
    last_choice_added DATETIME NOT NULL,   
    tier INTEGER NOT NULL,
    has_ever_tier INTEGER NOT NULL,
    voice INTEGER NOT NULL
);

CREATE TABLE choice (
    down_id INTEGER UNIQUE NOT NULL,
    up_id_1 INTEGER,
    up_id_2 INTEGER,
    up_id_3 INTEGER,
    time_chosen DATETIME NOT NULL,
    FOREIGN KEY (down_id) REFERENCES user(id)
);

CREATE TABLE reps (
    down_id INTEGER UNIQUE NOT NULL,
    up_id INTEGER NOT NULL,
    FOREIGN KEY (down_id) REFERENCES user(id)
);

CREATE TABLE rep_calculations (
    requester_id INTEGER NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    FOREIGN KEY (requester_id) REFERENCES user(id)
)
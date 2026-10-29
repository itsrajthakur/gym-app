CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'trainer', 'member')),
    phone TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS membership_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    duration_days INTEGER NOT NULL CHECK (duration_days > 0),
    price REAL NOT NULL CHECK (price >= 0),
    description TEXT
);

CREATE TABLE IF NOT EXISTS memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    plan_id INTEGER NOT NULL REFERENCES membership_plans(id),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'expired', 'frozen')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    membership_id INTEGER REFERENCES memberships(id),
    amount REAL NOT NULL CHECK (amount >= 0),
    method TEXT NOT NULL CHECK (method IN ('cash', 'card', 'upi')),
    paid_at TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    check_in_at TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'desk' CHECK (source IN ('self', 'desk'))
);

CREATE TABLE IF NOT EXISTS gym_classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    trainer_id INTEGER NOT NULL REFERENCES users(id),
    weekday INTEGER NOT NULL CHECK (weekday BETWEEN 0 AND 6),
    start_time TEXT NOT NULL,
    duration_min INTEGER NOT NULL CHECK (duration_min > 0),
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    description TEXT
);

CREATE TABLE IF NOT EXISTS class_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL REFERENCES gym_classes(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    session_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('booked', 'cancelled', 'attended')),
    created_at TEXT NOT NULL,
    UNIQUE (class_id, user_id, session_date)
);

CREATE TABLE IF NOT EXISTS workout_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL REFERENCES users(id),
    trainer_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plan_exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL REFERENCES workout_plans(id) ON DELETE CASCADE,
    exercise_name TEXT NOT NULL,
    sets INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    rest_sec INTEGER,
    day_label TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS workout_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    logged_on TEXT NOT NULL,
    exercise_name TEXT NOT NULL,
    sets INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    weight REAL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS ad_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    duration_days INTEGER NOT NULL CHECK (duration_days > 0),
    price REAL NOT NULL CHECK (price >= 0),
    description TEXT
);

CREATE TABLE IF NOT EXISTS advertisements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    advertiser_name TEXT NOT NULL,
    advertiser_phone TEXT,
    title TEXT NOT NULL,
    body TEXT,
    image_path TEXT,
    link_url TEXT,
    plan_id INTEGER NOT NULL REFERENCES ad_plans(id),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'paused', 'expired')),
    amount REAL NOT NULL CHECK (amount >= 0),
    method TEXT NOT NULL CHECK (method IN ('cash', 'card', 'upi')),
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_memberships_user ON memberships(user_id, start_date);
CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id, paid_at);
CREATE INDEX IF NOT EXISTS idx_attendance_user ON attendance(user_id, check_in_at);
CREATE INDEX IF NOT EXISTS idx_bookings_session ON class_bookings(class_id, session_date, status);
CREATE INDEX IF NOT EXISTS idx_workout_logs_user ON workout_logs(user_id, logged_on);
CREATE INDEX IF NOT EXISTS idx_ads_status ON advertisements(status, end_date);

from sqlalchemy import text


def apply_migrations(db):
    """
    Apply incremental schema changes to an existing database.
    Each migration checks if the change is needed before applying,
    so it is safe to run multiple times (idempotent).
    """
    _add_user_ban_columns(db)
    _add_rejected_job_status(db)
    _add_priority_window_column(db)


def _add_user_ban_columns(db):
    """Add is_banned, banned_at, ban_reason columns to users table."""
    conn = db.session.connection()

    # Check if is_banned column already exists
    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'users' AND column_name = 'is_banned'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN is_banned BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        print("Migration: added is_banned column to users table")

    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'users' AND column_name = 'banned_at'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN banned_at TIMESTAMPTZ"
        ))
        print("Migration: added banned_at column to users table")

    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'users' AND column_name = 'ban_reason'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN ban_reason VARCHAR(500)"
        ))
        print("Migration: added ban_reason column to users table")

    db.session.commit()


def _add_priority_window_column(db):
    """Add priority_window_end column to job_requests table."""
    conn = db.session.connection()

    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'job_requests' AND column_name = 'priority_window_end'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "ALTER TABLE job_requests ADD COLUMN priority_window_end TIMESTAMPTZ"
        ))
        print("Migration: added priority_window_end column to job_requests table")

    db.session.commit()


def _add_rejected_job_status(db):
    """Add 'rejected' value to the jobstatus enum type."""
    conn = db.session.connection()

    # Check if 'rejected' already exists in the enum
    result = conn.execute(text(
        "SELECT enumlabel FROM pg_enum "
        "JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
        "WHERE pg_type.typname = 'jobstatus' AND pg_enum.enumlabel = 'rejected'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "ALTER TYPE jobstatus ADD VALUE 'rejected'"
        ))
        print("Migration: added 'rejected' to jobstatus enum")

    db.session.commit()

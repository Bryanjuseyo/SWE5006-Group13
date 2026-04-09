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
    _add_cleaner_completed_job_status(db)
    _add_two_factor_columns(db)
    _add_cleaner_profiles_service_type_index(db)
    _add_users_role_ban_index(db)
    _add_availability_date_index(db)
    _add_availability_profile_dates_index(db)
    _add_job_requests_matching_index(db)
    _add_job_requests_matching_indexes_v2(db)


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


def _add_cleaner_completed_job_status(db):
    """Add 'cleaner_completed' value to the jobstatus enum type."""
    conn = db.session.connection()

    result = conn.execute(text(
        "SELECT enumlabel FROM pg_enum "
        "JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
        "WHERE pg_type.typname = 'jobstatus' AND pg_enum.enumlabel = 'cleaner_completed'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "ALTER TYPE jobstatus ADD VALUE 'cleaner_completed'"
        ))
        print("Migration: added 'cleaner_completed' to jobstatus enum")

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


def _add_two_factor_columns(db):
    """Add two_factor_enabled, two_factor_otp, two_factor_otp_expires columns to users table."""
    conn = db.session.connection()

    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'users' AND column_name = 'two_factor_enabled'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        print("Migration: added two_factor_enabled column to users table")

    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'users' AND column_name = 'two_factor_otp'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN two_factor_otp VARCHAR(255)"
        ))
        print("Migration: added two_factor_otp column to users table")

    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'users' AND column_name = 'two_factor_otp_expires'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN two_factor_otp_expires TIMESTAMPTZ"
        ))
        print("Migration: added two_factor_otp_expires column to users table")

    db.session.commit()


def _add_cleaner_profiles_service_type_index(db):
    """Add index on cleaner_profiles.service_type to speed up matching queries."""
    conn = db.session.connection()

    result = conn.execute(text(
        "SELECT 1 FROM pg_indexes "
        "WHERE tablename = 'cleaner_profiles' AND indexname = 'ix_cleaner_profiles_service_type'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "CREATE INDEX ix_cleaner_profiles_service_type ON cleaner_profiles (service_type)"
        ))
        print("Migration: added index on cleaner_profiles.service_type")

    db.session.commit()


def _add_users_role_ban_index(db):
    """Add composite index on users(role, is_banned) for cleaner matching filters."""
    conn = db.session.connection()

    result = conn.execute(text(
        "SELECT 1 FROM pg_indexes "
        "WHERE tablename = 'users' AND indexname = 'ix_users_role_is_banned'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "CREATE INDEX ix_users_role_is_banned ON users (role, is_banned)"
        ))
        print("Migration: added composite index on users (role, is_banned)")

    db.session.commit()


def _add_availability_date_index(db):
    """Add composite index on cleaner_availability (start_date, end_date) for date-range filtering."""
    conn = db.session.connection()

    result = conn.execute(text(
        "SELECT 1 FROM pg_indexes "
        "WHERE tablename = 'cleaner_availability' AND indexname = 'ix_cleaner_availability_dates'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "CREATE INDEX ix_cleaner_availability_dates ON cleaner_availability (start_date, end_date)"
        ))
        print("Migration: added composite index on cleaner_availability (start_date, end_date)")

    db.session.commit()


def _add_availability_profile_dates_index(db):
    """Add composite index on cleaner_availability for profile/date matching."""
    conn = db.session.connection()

    result = conn.execute(text(
        "SELECT 1 FROM pg_indexes "
        "WHERE tablename = 'cleaner_availability' "
        "AND indexname = 'ix_cleaner_availability_profile_dates'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "CREATE INDEX ix_cleaner_availability_profile_dates "
            "ON cleaner_availability (cleaner_profile_id, start_date, end_date)"
        ))
        print(
            "Migration: added composite index on cleaner_availability "
            "(cleaner_profile_id, start_date, end_date)"
        )

    db.session.commit()


def _add_job_requests_matching_index(db):
    """Add composite index on job_requests for the booked-cleaner subquery."""
    conn = db.session.connection()

    result = conn.execute(text(
        "SELECT 1 FROM pg_indexes "
        "WHERE tablename = 'job_requests' AND indexname = 'ix_job_requests_cleaner_date_status'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "CREATE INDEX ix_job_requests_cleaner_date_status "
            "ON job_requests (cleaner_id, preferred_date, status) "
            "WHERE cleaner_id IS NOT NULL AND deleted_at IS NULL"
        ))
        print("Migration: added composite index on job_requests (cleaner_id, preferred_date, status)")

    db.session.commit()


def _add_job_requests_matching_indexes_v2(db):
    """Add composite indexes on job_requests matching the current auto-matching query."""
    conn = db.session.connection()

    result = conn.execute(text(
        "SELECT 1 FROM pg_indexes "
        "WHERE tablename = 'job_requests' "
        "AND indexname = 'ix_job_requests_cleaner_date_status_deleted'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "CREATE INDEX ix_job_requests_cleaner_date_status_deleted "
            "ON job_requests (cleaner_id, preferred_date, status, deleted_at)"
        ))
        print(
            "Migration: added composite index on job_requests "
            "(cleaner_id, preferred_date, status, deleted_at)"
        )

    result = conn.execute(text(
        "SELECT 1 FROM pg_indexes "
        "WHERE tablename = 'job_requests' "
        "AND indexname = 'ix_job_requests_date_status_deleted'"
    ))
    if result.fetchone() is None:
        conn.execute(text(
            "CREATE INDEX ix_job_requests_date_status_deleted "
            "ON job_requests (preferred_date, status, deleted_at)"
        ))
        print(
            "Migration: added composite index on job_requests "
            "(preferred_date, status, deleted_at)"
        )

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

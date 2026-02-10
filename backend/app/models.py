from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
import enum

db = SQLAlchemy()
bcrypt = Bcrypt()

# =============================================
# ENUMS
# =============================================


class UserRole(enum.Enum):
    end_user = 'end_user'
    cleaner = 'cleaner'
    administrator = 'administrator'


class ServiceType(enum.Enum):
    partial = 'partial'
    full = 'full'

# =============================================
# USER (Authentication)
# =============================================


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.end_user, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime(timezone=True), nullable=True)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    cleaner_profile = db.relationship('CleanerProfile', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role.value,
            'created_at': self.created_at.isoformat()
        }

# =============================================
# USER PROFILE (All Users)
# =============================================


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'address': self.address,
            'city': self.city
        }

# =============================================
# CLEANING SERVICES LOOKUP
# =============================================


class CleaningService(db.Model):
    __tablename__ = 'cleaning_services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

# =============================================
# CLEANER PROFILE
# =============================================


class CleanerProfile(db.Model):
    __tablename__ = 'cleaner_profiles'

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    service_type = db.Column(db.Enum(ServiceType), nullable=False)
    hourly_rate = db.Column(db.Numeric(10, 2))
    years_experience = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    offered_services = db.relationship('CleanerOfferedService', backref='cleaner_profile', cascade='all, delete-orphan')
    availability = db.relationship('CleanerAvailability', backref='cleaner_profile', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'service_type': self.service_type.value,
            'hourly_rate': float(self.hourly_rate) if self.hourly_rate else None,
            'years_experience': self.years_experience,
            'offered_services': [s.to_dict() for s in self.offered_services],
            'availability': [a.to_dict() for a in self.availability]
        }

# =============================================
# CLEANER OFFERED SERVICES
# =============================================


class CleanerOfferedService(db.Model):
    __tablename__ = 'cleaner_offered_services'

    id = db.Column(db.BigInteger, primary_key=True)
    cleaner_profile_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            'cleaner_profiles.id',
            ondelete='CASCADE'),
        nullable=False)
    cleaning_service_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'cleaning_services.id',
            ondelete='CASCADE'),
        nullable=False)
    custom_price = db.Column(db.Numeric(10, 2))

    cleaning_service = db.relationship('CleaningService')

    __table_args__ = (
        db.UniqueConstraint('cleaner_profile_id', 'cleaning_service_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'cleaning_service': self.cleaning_service.to_dict(),
            'custom_price': float(self.custom_price) if self.custom_price else None
        }

# =============================================
# CLEANER AVAILABILITY
# =============================================


class CleanerAvailability(db.Model):
    __tablename__ = 'cleaner_availability'

    id = db.Column(db.BigInteger, primary_key=True)
    cleaner_profile_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            'cleaner_profiles.id',
            ondelete='CASCADE'),
        nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)

    __table_args__ = (
        db.CheckConstraint('end_date >= start_date'),
        db.CheckConstraint('end_time > start_time OR end_time IS NULL'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'cleaner_profile_id': self.cleaner_profile_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }

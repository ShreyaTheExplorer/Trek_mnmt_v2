from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    # Roles: 'admin', 'staff', 'user'
    role = db.Column(db.String(20), nullable=False, default='user')
    # Status: 'active', 'inactive', 'blacklisted'
    status = db.Column(db.String(20), nullable=False, default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Profile fields
    age = db.Column(db.Integer, nullable=True)
    emergency_contact = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)

    # Relationships
    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    assigned_treks = db.relationship('Trek', backref='assigned_staff', lazy='dynamic', foreign_keys='Trek.assigned_staff_id')
    bookings = db.relationship('Booking', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self) -> bool:
        return self.status == 'active'

    def to_dict(self, include_profile=True):
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'status': self.status,
            'age': self.age,
            'emergency_contact': self.emergency_contact,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_profile and self.role == 'staff' and self.staff_profile:
            data['staff_profile'] = self.staff_profile.to_dict()
        return data


class StaffProfile(db.Model):
    __tablename__ = 'staff_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    contact_details = db.Column(db.Text, nullable=True)
    specialization = db.Column(db.String(150), nullable=True) # e.g. High Altitude, First Aid, Navigation
    # Status: 'active', 'inactive'
    status = db.Column(db.String(20), nullable=False, default='active')
    joined_on = db.Column(db.Date, default=date.today, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'contact_details': self.contact_details,
            'specialization': self.specialization,
            'status': self.status,
            'joined_on': self.joined_on.isoformat() if isinstance(self.joined_on, (date, datetime)) else self.joined_on
        }


class Trek(db.Model):
    __tablename__ = 'treks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    location = db.Column(db.String(150), nullable=False)
    # Difficulty: 'Easy', 'Moderate', 'Hard'
    difficulty = db.Column(db.String(20), nullable=False, default='Moderate')
    duration_days = db.Column(db.Integer, nullable=False, default=1)
    total_slots = db.Column(db.Integer, nullable=False, default=20)
    available_slots = db.Column(db.Integer, nullable=False, default=20)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    # Status: 'Pending', 'Approved', 'Open', 'Closed', 'Completed'
    status = db.Column(db.String(20), nullable=False, default='Pending')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False) # Soft delete flag

    # Relationships
    bookings = db.relationship('Booking', backref='trek', lazy='dynamic', cascade='all, delete-orphan')

    def recalculate_available_slots(self):
        """
        Recalculates available slots by subtracting all active 'Booked' participants.
        """
        active_bookings = self.bookings.filter_by(status='Booked').all()
        booked_participants = sum(b.participants_count for b in active_bookings)
        self.available_slots = max(0, self.total_slots - booked_participants)
        return self.available_slots

    def to_dict(self):
        staff_name = self.assigned_staff.name if self.assigned_staff else None
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'difficulty': self.difficulty,
            'duration_days': self.duration_days,
            'total_slots': self.total_slots,
            'available_slots': self.available_slots,
            'assigned_staff_id': self.assigned_staff_id,
            'assigned_staff_name': staff_name,
            'status': self.status,
            'start_date': self.start_date.isoformat() if isinstance(self.start_date, (date, datetime)) else self.start_date,
            'end_date': self.end_date.isoformat() if isinstance(self.end_date, (date, datetime)) else self.end_date,
            'description': self.description,
            'instructions': self.instructions,
            'price': self.price,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False, index=True)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # Status: 'Booked', 'Cancelled', 'Completed'
    status = db.Column(db.String(20), nullable=False, default='Booked')
    # Payment Status: 'Pending', 'Paid', 'NA'
    payment_status = db.Column(db.String(20), nullable=False, default='Pending')
    participants_count = db.Column(db.Integer, nullable=False, default=1)
    cancelled_at = db.Column(db.DateTime, nullable=True)

    @classmethod
    def has_active_booking(cls, user_id: int, trek_id: int) -> bool:
        """
        Code check preventing duplicate active bookings for the same user and trek.
        """
        return cls.query.filter_by(
            user_id=user_id,
            trek_id=trek_id,
            status='Booked'
        ).first() is not None

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'user_email': self.user.email if self.user else None,
            'trek_id': self.trek_id,
            'trek_name': self.trek.name if self.trek else None,
            'trek_start_date': self.trek.start_date.isoformat() if self.trek and self.trek.start_date else None,
            'trek_end_date': self.trek.end_date.isoformat() if self.trek and self.trek.end_date else None,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'status': self.status,
            'payment_status': self.payment_status,
            'participants_count': self.participants_count,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None
        }


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_read': self.is_read
        }

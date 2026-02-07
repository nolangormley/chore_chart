from datetime import datetime
from database import db

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    total_points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    pronouns = db.Column(db.String(20))
    email = db.Column(db.String(120))
    profile_picture = db.Column(db.String(255))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'total_points': self.total_points,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'pronouns': self.pronouns,
            'email': self.email,
            'profile_picture': self.profile_picture
        }

class Chore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    points = db.Column(db.Integer, nullable=False)
    is_recurring = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'points': self.points,
            'is_recurring': self.is_recurring,
            'created_at': self.created_at.isoformat()
        }
        
        if self.is_recurring and self.logs:
            # Find the most recent log
            last_log = max(self.logs, key=lambda x: x.completed_at)
            data['last_completed_at'] = last_log.completed_at.isoformat()
            
        return data

class ChoreLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chore_id = db.Column(db.Integer, db.ForeignKey('chore.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    points_earned = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    chore = db.relationship('Chore', backref=db.backref('logs', lazy=True))
    user = db.relationship('User', backref=db.backref('logs', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'chore_id': self.chore_id,
            'user_id': self.user_id,
            'points_earned': self.points_earned,
            'completed_at': self.completed_at.isoformat(),
            'chore_title': self.chore.title if self.chore else 'Unknown',
            'username': self.user.username if self.user else 'Unknown'
        }

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from app.extensions import db
from app.models import User

def auto_seed():
    with app.app_context():
        print("Resetting database...")
        db.drop_all()
        db.create_all()
        
        user = User(username="admin")
        user.set_password("password")
        
        db.session.add(user)
        db.session.commit()
        print("Default user created: admin / password")

if __name__ == '__main__':
    auto_seed()

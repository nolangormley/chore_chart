from app import app, db
from models import User

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

from app import app, db
from models import User

def seed_admin():
    with app.app_context():
        # WARNING: This will reset the database to ensure schema changes are applied
        print("Recreating database...")
        db.drop_all()
        db.create_all()
        
        username = input("Enter admin username: ")
        password = input("Enter admin password: ")
        
        if not username or not password:
            print("Username and password required.")
            return

        user = User(username=username)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        print(f"User '{username}' created successfully!")

if __name__ == '__main__':
    seed_admin()

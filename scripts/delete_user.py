import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from app.extensions import db
from app.models import User

def delete_user(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"User {user.username} found. Deleting...")
            
            # Since User has cascading relationships (e.g., logs, schedules) we should define that, 
            # currently SQLAlchemy cascade defaults might not be set for 'logs' or 'schedules' backrefs, 
            # but usually 'ondelete' is needed in DB definition or SQLAlchemy handles manual delete.
            # However, simpler manual deletion of related records is safer if unsure.
            
            # Delete related logs
            if user.logs:
                for log in user.logs:
                    db.session.delete(log)
            
            # Delete related schedules if any
            if hasattr(user, 'schedules'):
                for schedule in user.schedules:
                    db.session.delete(schedule)

            db.session.delete(user)
            db.session.commit()
            print(f"User {username} and related data deleted successfully.")
        else:
            print(f"User {username} not found.")

if __name__ == "__main__":
    delete_user("test_pagination_user")

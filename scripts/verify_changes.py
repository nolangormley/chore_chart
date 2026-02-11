import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from app.extensions import db
from app.models import Chore, User, ChoreLog
from datetime import datetime, timedelta

def verify():
    with app.app_context():
        # Create a test user if needed
        user = User.query.first()
        if not user:
            user = User(username="TestVerifier")
            db.session.add(user)
            db.session.commit()

        # Create a test recurring chore
        chore = Chore(title="Test Recurring Chore", points=10, is_recurring=True)
        db.session.add(chore)
        db.session.commit()

        print(f"Created chore: {chore.title} (ID: {chore.id})")

        # Initial check - should have no last_completed_at
        data = chore.to_dict()
        if 'last_completed_at' in data:
            print("FAILURE: New chore should not have last_completed_at")
        else:
            print("SUCCESS: New chore correctly has no last_completed_at")

        # Add a log
        now = datetime.utcnow()
        log = ChoreLog(chore_id=chore.id, user_id=user.id, points_earned=10, completed_at=now)
        db.session.add(log)
        db.session.commit()

        # Check again
        # We might need to refresh the chore or its logs relationship
        db.session.expire(chore)
        
        data = chore.to_dict()
        expected_date = now.isoformat()
        if 'last_completed_at' in data and data['last_completed_at'] == expected_date:
            print(f"SUCCESS: Chore has last_completed_at: {data['last_completed_at']}")
        else:
            print(f"FAILURE: Expected {expected_date}, got {data.get('last_completed_at')}")

        # Clean up
        db.session.delete(log)
        db.session.delete(chore)
        db.session.commit()

if __name__ == "__main__":
    verify()

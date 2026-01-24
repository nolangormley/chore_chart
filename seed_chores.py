from app import app, db, Chore, User, ChoreLog
from datetime import datetime, timedelta
import random

def seed_data():
    with app.app_context():
        print("Starting seed process...")

        # 1. Create Users
        users_data = ["Nolan", "Alice", "Bob", "Charlie"]
        users = []
        for name in users_data:
            user = User.query.filter_by(username=name).first()
            if not user:
                user = User(username=name)
                db.session.add(user)
                print(f"Created user: {name}")
            else:
                print(f"User exists: {name}")
            users.append(user)
        db.session.commit()
        
        # Refresh users to get IDs
        users = User.query.filter(User.username.in_(users_data)).all()

        # 2. Create Chores
        chores_data = [
            {"title": "Wash Dishes", "points": 10, "is_recurring": True, "description": "Wash, dry, and put away all dishes."},
            {"title": "Take Out Trash", "points": 15, "is_recurring": True, "description": "Empty kitchen and bathroom bins."},
            {"title": "Vacuum Living Room", "points": 20, "is_recurring": True, "description": "Vacuum the rug and floor."},
            {"title": "Clean Bathroom", "points": 30, "is_recurring": True, "description": "Scrub toilet, sink, and shower."},
            {"title": "Walk the Dog", "points": 25, "is_recurring": True, "description": "30 minute walk around the neighborhood."},
            {"title": "Mow the Lawn", "points": 50, "is_recurring": True, "description": "Front and back yard."},
            {"title": "Water Plants", "points": 10, "is_recurring": True, "description": "Water indoor and balcony plants."},
            {"title": "Fold Laundry", "points": 20, "is_recurring": True, "description": "Fold and put away clothes."},
            {"title": "Clean Windows", "points": 40, "is_recurring": False, "description": "Wipe down all windows inside."},
            {"title": "Organize Garage", "points": 100, "is_recurring": False, "description": "Deep clean and organize shelves."}
        ]

        created_chores = []
        for data in chores_data:
            chore = Chore.query.filter_by(title=data['title'], is_deleted=False).first()
            if not chore:
                chore = Chore(
                    title=data['title'],
                    points=data['points'],
                    is_recurring=data['is_recurring'],
                    description=data['description']
                )
                db.session.add(chore)
                print(f"Added chore: {data['title']}")
            created_chores.append(chore)
        
        db.session.commit()
        
        # Refresh chores to get IDs
        # We need actual objects bound to session or re-queried
        all_chores = Chore.query.filter_by(is_deleted=False).all()

        # 3. Generate History (Last 10 days)
        print("Generating historical data...")
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=10)
        
        # Generate 50 random logs
        for _ in range(50):
            user = random.choice(users)
            chore = random.choice(all_chores)
            
            # Random time in the last 10 days
            random_days = random.uniform(0, 10)
            completed_time = end_date - timedelta(days=random_days)
            
            log = ChoreLog(
                chore_id=chore.id,
                user_id=user.id,
                points_earned=chore.points,
                completed_at=completed_time
            )
            
            # Update user points
            user.total_points += chore.points
            
            db.session.add(log)
        
        db.session.commit()
        print("Historical data seeded successfully!")

if __name__ == '__main__':
    seed_data()

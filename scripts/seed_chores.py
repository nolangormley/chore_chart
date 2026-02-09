from app import app, db, Chore, User, ChoreLog
from datetime import datetime, timedelta
import random

def seed_data():
    with app.app_context():
        print("Starting seed process...")

        # 1. Create/Update Users with Profile Pictures
        # Using DiceBear for random avatars
        users_data = [
            {"username": "Nolan", "profile_picture": "https://api.dicebear.com/9.x/avataaars/svg?seed=Nolan"},
            {"username": "Alice", "profile_picture": "https://api.dicebear.com/9.x/avataaars/svg?seed=Alice"},
            {"username": "Bob", "profile_picture": "https://api.dicebear.com/9.x/avataaars/svg?seed=Bob"},
            {"username": "Charlie", "profile_picture": "https://api.dicebear.com/9.x/avataaars/svg?seed=Charlie"}
        ]
        
        users_map = {}
        for data in users_data:
            user = User.query.filter_by(username=data['username']).first()
            if not user:
                user = User(username=data['username'])
                print(f"Created user: {data['username']}")
            else:
                print(f"Updating user: {data['username']}")
            
            # Set profile picture
            user.profile_picture = data['profile_picture']
            db.session.add(user)
            users_map[data['username']] = user
        
        db.session.commit()
        
        # Get list of user objects
        users = list(users_map.values())

        # 2. Create/Update Chores with Locations
        chores_data = [
            {"title": "Wash Dishes", "points": 10, "is_recurring": True, "description": "Wash, dry, and put away all dishes.", "location": "Inside"},
            {"title": "Take Out Trash", "points": 15, "is_recurring": True, "description": "Empty kitchen and bathroom bins.", "location": "Inside"},
            {"title": "Vacuum Living Room", "points": 20, "is_recurring": True, "description": "Vacuum the rug and floor.", "location": "Inside"},
            {"title": "Clean Bathroom", "points": 30, "is_recurring": True, "description": "Scrub toilet, sink, and shower.", "location": "Inside"},
            {"title": "Walk the Dog", "points": 25, "is_recurring": True, "description": "30 minute walk around the neighborhood.", "location": "Outside"},
            {"title": "Mow the Lawn", "points": 50, "is_recurring": True, "description": "Front and back yard.", "location": "Outside"},
            {"title": "Water Plants", "points": 10, "is_recurring": True, "description": "Water indoor and balcony plants.", "location": "Inside"},
            {"title": "Fold Laundry", "points": 20, "is_recurring": True, "description": "Fold and put away clothes.", "location": "Inside"},
            {"title": "Clean Windows", "points": 40, "is_recurring": False, "description": "Wipe down all windows inside.", "location": "Inside"},
            {"title": "Organize Garage", "points": 100, "is_recurring": False, "description": "Deep clean and organize shelves.", "location": "Garage"},
            {"title": "Wash Car", "points": 45, "is_recurring": False, "description": "Wash and wax the car.", "location": "Outside"},
            {"title": "Weed Garden", "points": 35, "is_recurring": True, "description": "Pull weeds from flower beds.", "location": "Outside"}
        ]

        all_chores = []
        for data in chores_data:
            chore = Chore.query.filter_by(title=data['title']).first()
            if not chore:
                chore = Chore(
                    title=data['title'],
                    points=data['points'],
                    is_recurring=data['is_recurring'],
                    description=data['description'],
                    location=data.get('location', 'Inside')
                )
                print(f"Created chore: {data['title']}")
            else:
                # Update existing fields
                chore.points = data['points']
                chore.description = data['description']
                chore.location = data.get('location', 'Inside')
                chore.is_recurring = data['is_recurring']
                print(f"Updated chore: {data['title']}")
                
            db.session.add(chore)
            all_chores.append(chore)
        
        db.session.commit()
        
        # 3. Generate History (Last 10 days) if needed
        # We can append random logs to existing history without clearing? 
        # Or maybe just skip if history exists? 
        # Let's add some fresh history.
        
        print("Adding some historical data...")
        end_date = datetime.utcnow()
        
        for _ in range(20): # Add 20 new logs
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
            
            # Update user points (approximate, since we are re-seeding)
            user.total_points += chore.points
            
            db.session.add(log)
        
        db.session.commit()
        print("Database seeded successfully with Users, Pictures, Chores, Locations, and History!")

if __name__ == '__main__':
    seed_data()

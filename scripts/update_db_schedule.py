import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from app.extensions import db
from sqlalchemy import text

def add_schedule_table():
    with app.app_context():
        # Create table if not exists
        # Since we use SQLAlchemy models, typically db.create_all() works but only for new tables.
        # But let's be safe and try to create it specifically.
        
        # Check if table exists
        with db.engine.connect() as conn:
            try:
                conn.execute(text("SELECT 1 FROM chore_schedule LIMIT 1"))
                print("Table 'chore_schedule' already exists.")
            except Exception:
                print("Creating 'chore_schedule' table...")
                db.create_all() # This creates all tables defined in models that don't exist
                print("Table created.")

if __name__ == "__main__":
    add_schedule_table()

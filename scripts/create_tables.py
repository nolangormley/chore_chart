import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

from app import app
from app.extensions import db

def create_table():
    with app.app_context():
        db.create_all()
        print("Created tables.")

if __name__ == "__main__":
    create_table()

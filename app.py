from flask import Flask, render_template, request, jsonify
from database import db
from models import User, Chore, ChoreLog
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chore_chart.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stats')
def stats():
    return render_template('stats.html')

# API Routes
@app.route('/api/users', methods=['GET', 'POST'])
def handle_users():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        if User.query.filter_by(username=username).first():
             return jsonify({'error': 'Username already exists'}), 400
        
        user = User(username=username)
        db.session.add(user)
        db.session.commit()
        return jsonify(user.to_dict()), 201
    
    users = User.query.order_by(User.total_points.desc()).all()
    return jsonify([u.to_dict() for u in users])

@app.route('/api/chores', methods=['GET', 'POST'])
def handle_chores():
    if request.method == 'POST':
        data = request.json
        title = data.get('title')
        points = data.get('points')
        
        if not title or not points:
            return jsonify({'error': 'Title and points are required'}), 400
            
        chore = Chore(
            title=title,
            description=data.get('description'),
            points=int(points),
            is_recurring=data.get('is_recurring', False)
        )
        db.session.add(chore)
        db.session.commit()
        return jsonify(chore.to_dict()), 201

    chores = Chore.query.filter_by(is_deleted=False).order_by(Chore.created_at.desc()).all()
    return jsonify([c.to_dict() for c in chores])

@app.route('/api/chores/<int:chore_id>/complete', methods=['POST'])
def complete_chore(chore_id):
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
        
    chore = Chore.query.get_or_404(chore_id)
    user = User.query.get_or_404(user_id)
    
    # Create log
    log = ChoreLog(
        chore_id=chore.id,
        user_id=user.id,
        points_earned=chore.points
    )
    
    # Update user points
    user.total_points += chore.points
    
    # Handle non-recurring chores
    if not chore.is_recurring:
        chore.is_deleted = True
        
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'message': 'Chore completed',
        'points_earned': chore.points,
        'user_total': user.total_points
    })

@app.route('/api/chores/<int:chore_id>', methods=['DELETE'])
def delete_chore(chore_id):
    chore = Chore.query.get_or_404(chore_id)
    chore.is_deleted = True
    db.session.commit()
    return jsonify({'message': 'Chore deleted'})

@app.route('/api/stats/history', methods=['GET'])
def get_stats_history():
    logs = ChoreLog.query.order_by(ChoreLog.completed_at.desc()).limit(50).all()
    return jsonify([l.to_dict() for l in logs])

@app.route('/api/stats/charts', methods=['GET'])
def get_chart_data():
    # 1. Points Distribution (Total points per user)
    users = User.query.all()
    distribution = {u.username: u.total_points for u in users if u.total_points > 0}
    
    # 2. Activity / Momentum (Last 7 days)
    # This is a bit complex in SQL, we'll do simple python aggregation for prototype
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    logs = ChoreLog.query.filter(ChoreLog.completed_at >= seven_days_ago).all()
    
    # Organize by date -> user -> points
    timeline = {} # "YYYY-MM-DD": {"UserA": 10, "UserB": 20}
    
    for log in logs:
        date_str = log.completed_at.strftime('%Y-%m-%d')
        if date_str not in timeline:
            timeline[date_str] = {}
        
        user_name = log.user.username
        timeline[date_str][user_name] = timeline[date_str].get(user_name, 0) + log.points_earned

    # Sort timeline
    sorted_dates = sorted(timeline.keys())
    
    return jsonify({
        'distribution': distribution,
        'timeline': {
            'dates': sorted_dates,
            'data': timeline
        }
    })

if __name__ == '__main__':
    app.run(debug=True)

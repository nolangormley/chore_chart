from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.models import ChoreLog, User
from app.extensions import db
from datetime import datetime, timedelta

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/api/stats/history', methods=['GET'])
@login_required
def get_stats_history():
    """
    Get paginated activity history
    ---
    tags:
      - Stats
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 10
    responses:
      200:
        description: List of activity logs with pagination info
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    pagination = ChoreLog.query.order_by(ChoreLog.completed_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'logs': [l.to_dict() for l in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })

@stats_bp.route('/api/stats/charts', methods=['GET'])
@login_required
def get_chart_data():
    """
    Get data for charts
    ---
    tags:
      - Stats
    responses:
      200:
        description: Objects containing data for distribution and timeline charts
    """
    # 1. Points Distribution (Total points per user)
    users = User.query.all()
    distribution = {u.username: u.total_points for u in users if u.total_points > 0}
    
    # 2. Activity / Momentum (Last 7 days)
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

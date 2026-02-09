from flask import Blueprint, render_template
from flask_login import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    return render_template('index.html')

@main_bp.route('/stats')
@login_required
def stats():
    return render_template('stats.html')

@main_bp.route('/user/<int:user_id>')
@login_required
def user_details(user_id):
    return render_template('user_details.html', user_id=user_id)

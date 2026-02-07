from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import db
from models import User, Chore, ChoreLog, ChoreSchedule
from flasgger import Swagger
from werkzeug.utils import secure_filename
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from email.mime.base import MIMEBase
from email import encoders
from ics import Calendar, Event
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-this-for-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///chore_chart.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Mail Config
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

swagger = Swagger(app)
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/stats')
@login_required
def stats():
    return render_template('stats.html')

# Auth Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# API Routes
@app.route('/api/users', methods=['GET', 'POST'])
@login_required
def handle_users():
    """
    Manage users
    ---
    tags:
      - Users
    parameters:
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            username:
              type: string
    responses:
      200:
        description: List of users
      201:
        description: User created
      400:
        description: Invalid input or username exists
    """
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

@app.route('/user/<int:user_id>')
@login_required
def user_details(user_id):
    return render_template('user_details.html', user_id=user_id)

@app.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    """
    Get user details
    ---
    tags:
      - Users
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: User details
      404:
        description: User not found
    """
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """
    Update user details
    ---
    tags:
      - Users
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            first_name:
              type: string
            last_name:
              type: string
            pronouns:
              type: string
            email:
              type: string
    responses:
      200:
        description: User updated
      404:
        description: User not found
    """
    user = User.query.get_or_404(user_id)
    data = request.json
    
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'pronouns' in data:
        user.pronouns = data['pronouns']
    if 'email' in data:
        user.email = data['email']
        
    db.session.commit()
    return jsonify(user.to_dict())

@app.route('/api/users/<int:user_id>/upload-picture', methods=['POST'])
@login_required
def upload_profile_picture(user_id):
    """
    Upload profile picture
    ---
    tags:
      - Users
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
      - name: file
        in: formData
        type: file
        required: true
    responses:
      200:
        description: Picture uploaded
      400:
        description: No file part
    """
    user = User.query.get_or_404(user_id)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(f"user_{user_id}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        user.profile_picture = url_for('static', filename=f'uploads/{filename}')
        db.session.commit()
        return jsonify({'message': 'File uploaded', 'url': user.profile_picture})

@app.route('/api/chores', methods=['GET', 'POST'])
@login_required
def handle_chores():
    """
    Manage chores
    ---
    tags:
      - Chores
    parameters:
      - name: body
        in: body
        required: false
        schema:
          type: object
          required:
            - title
            - points
          properties:
            title:
              type: string
            description:
              type: string
            location:
              type: string
            points:
              type: integer
            is_recurring:
              type: boolean
    responses:
      200:
        description: List of active chores
      201:
        description: Chore created
      400:
        description: Missing required fields
    """
    if request.method == 'POST':
        data = request.json
        title = data.get('title')
        points = data.get('points')
        
        if not title or not points:
            return jsonify({'error': 'Title and points are required'}), 400
            
        chore = Chore(
            title=title,
            description=data.get('description'),
            location=data.get('location', 'Inside'),
            points=int(points),
            is_recurring=data.get('is_recurring', False)
        )
        db.session.add(chore)
        db.session.commit()
        return jsonify(chore.to_dict()), 201

    chores = Chore.query.filter_by(is_deleted=False).order_by(Chore.created_at.desc()).all()
    return jsonify([c.to_dict() for c in chores])

@app.route('/api/chores/<int:chore_id>', methods=['PUT', 'DELETE'])
@login_required
def update_delete_chore(chore_id):
    """
    Update or Delete a chore
    ---
    tags:
      - Chores
    parameters:
      - name: chore_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            title:
              type: string
            description:
              type: string
            location:
              type: string
            points:
              type: integer
            is_recurring:
              type: boolean
    responses:
      200:
        description: Chore updated/deleted
      404:
        description: Chore not found
    """
    chore = Chore.query.get_or_404(chore_id)
    
    if request.method == 'DELETE':
        chore.is_deleted = True
        db.session.commit()
        return jsonify({'message': 'Chore deleted'})

    data = request.json
    
    if 'title' in data:
        chore.title = data['title']
    if 'description' in data:
        chore.description = data['description']
    if 'location' in data:
        chore.location = data['location']
    if 'points' in data:
        chore.points = int(data['points'])
    if 'is_recurring' in data:
        chore.is_recurring = data['is_recurring']
        
    db.session.commit()
    return jsonify(chore.to_dict())

@app.route('/api/chores/<int:chore_id>/complete', methods=['POST'])
@login_required
def complete_chore(chore_id):
    """
    Mark a chore as complete
    ---
    tags:
      - Chores
    parameters:
      - name: chore_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
          properties:
            user_id:
              type: integer
    responses:
      200:
        description: Chore completed successfully
      400:
        description: User ID is required
      404:
        description: Chore or User not found
    """
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
@login_required
def delete_chore(chore_id):
    """
    Delete (soft delete) a chore
    ---
    tags:
      - Chores
    parameters:
      - name: chore_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Chore deleted
      404:
        description: Chore not found
    """
    chore = Chore.query.get_or_404(chore_id)
    chore.is_deleted = True
    db.session.commit()
    return jsonify({'message': 'Chore deleted'})

@app.route('/api/stats/history', methods=['GET'])
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

@app.route('/api/stats/charts', methods=['GET'])
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

@app.route('/api/chores/<int:chore_id>/invite', methods=['POST'])
@login_required
def send_calendar_invite(chore_id):
    """
    Send Google Calendar Invite
    ---
    tags:
      - Chores
    parameters:
      - name: chore_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: integer
            datetime:
              type: string
    responses:
      200:
        description: Invite sent successfully
      400:
        description: User ID or Datetime missing
      404:
        description: User or Chore not found
      500:
        description: Failed to send email
    """
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
        
    dt_str = data.get('datetime')
    if not dt_str:
        return jsonify({'error': 'Datetime is required'}), 400
        
    try:
        chore = Chore.query.get_or_404(chore_id)
        user = User.query.get_or_404(user_id)
        
        if not user.email:
            return jsonify({'error': 'User does not have an email address set up.'}), 400
            
        print(f"Preparing invite for {user.email} concerning {chore.title} at {dt_str}")
        
        # Create Calendar Event
        c = Calendar()
        e = Event()
        e.name = f"Chore: {chore.title}"
        e.begin = dt_str
        e.description = f"Complete chore: {chore.title}. Points: {chore.points}"
        if chore.description:
            e.description += f"\n\nDescription: {chore.description}"
        c.events.add(e)
        
        # Save Schedule to DB
        try:
            dt_parse = dt_str
            if dt_parse.endswith('Z'):
                dt_parse = dt_parse[:-1]
            scheduled_dt = datetime.fromisoformat(dt_parse)
            
            schedule = ChoreSchedule(
                chore_id=chore.id,
                user_id=user.id,
                scheduled_at=scheduled_dt
            )
            db.session.add(schedule)
            db.session.commit()
        except Exception as schedule_err:
            print(f"Error saving schedule: {schedule_err}")
        
        ics_content = str(c)
        
        # Handle Recurrence
        recurrence = data.get('recurrence')
        if recurrence:
            rrule = None
            if recurrence == 'weekly':
                rrule = 'FREQ=WEEKLY'
            elif recurrence == 'biweekly':
                rrule = 'FREQ=WEEKLY;INTERVAL=2'
            elif recurrence == 'monthly':
                rrule = 'FREQ=MONTHLY'
                
            if rrule:
                # Inject RRULE before END:VEVENT
                ics_content = ics_content.replace('END:VEVENT', f'RRULE:{rrule}\nEND:VEVENT')
        
        # Create Email (Mock)
        msg = MIMEMultipart()
        sender = app.config.get('MAIL_DEFAULT_SENDER')
        msg['From'] = sender
        msg['To'] = user.email
        msg['Subject'] = f"Chore Reminder: {chore.title}"
        
        body = f"Hello {user.username},\n\nPlease find attached a calendar invite for your chore: {chore.title}."
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach ICS
        part = MIMEBase('text', 'calendar', method='REQUEST', name='invite.ics')
        part.set_payload(ics_content)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="invite.ics"')
        msg.attach(part)

        # Send Email
        server_conf = app.config.get('MAIL_SERVER')
        username_conf = app.config.get('MAIL_USERNAME')
        password_conf = app.config.get('MAIL_PASSWORD')
        port_conf = app.config.get('MAIL_PORT')
        
        if server_conf and username_conf and password_conf:
             try:
                 with smtplib.SMTP(server_conf, port_conf) as server:
                    if app.config.get('MAIL_USE_TLS'):
                        server.starttls()
                    server.login(username_conf, password_conf)
                    server.send_message(msg)
                 print(f"Sent email to {user.email}")
                 return jsonify({'message': 'Calendar invite sent to ' + user.email})
             except Exception as smtp_err:
                 print(f"SMTP Error: {smtp_err}")
                 return jsonify({'error': f'Failed to send email: {str(smtp_err)}'}), 500
        else:
            print("--- EMAIL (MOCK - MISSING CONFIG) ---")
            print(f"To: {user.email}")
            print(f"Subject: {msg['Subject']}")
            return jsonify({'message': 'Calendar invite generated (but email config missing)'})
        
    except Exception as e:
        print(f"Error sending invite: {e}")
        return jsonify({'error': f'Failed to send invite: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

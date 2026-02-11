from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required
from app.models import Chore, User, ChoreLog, ChoreSchedule
from app.extensions import db
from datetime import datetime
from ics import Calendar, Event
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib

chores_bp = Blueprint('chores', __name__)

@chores_bp.route('/api/chores', methods=['GET', 'POST'])
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

@chores_bp.route('/api/chores/<int:chore_id>', methods=['PUT', 'DELETE'])
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

@chores_bp.route('/api/chores/<int:chore_id>/complete', methods=['POST'])
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

@chores_bp.route('/api/chores/<int:chore_id>', methods=['DELETE'])
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

@chores_bp.route('/api/chores/<int:chore_id>/invite', methods=['POST'])
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
        sender = current_app.config.get('MAIL_DEFAULT_SENDER')
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
        api_key = current_app.config.get('MAIL_API_KEY')
        server_conf = current_app.config.get('MAIL_SERVER')
        username_conf = current_app.config.get('MAIL_USERNAME')
        password_conf = current_app.config.get('MAIL_PASSWORD')
        port_conf = current_app.config.get('MAIL_PORT')
        sender = current_app.config.get('MAIL_DEFAULT_SENDER')
        
        if api_key:
            # Send using Brevo API (v3) - Works on PythonAnywhere Free Tier
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json"
            }
            
            try:
                import requests
                import base64
                
                encoded_ics = base64.b64encode(ics_content.encode('utf-8')).decode('utf-8')
                
                payload = {
                    "sender": {"email": sender, "name": "Chore Chart"},
                    "to": [{"email": user.email, "name": user.username}],
                    "subject": f"Chore Reminder: {chore.title}",
                    "htmlContent": f"<html><body><p>Hello {user.username},</p><p>Please find attached a calendar invite for your chore: {chore.title}.</p></body></html>",
                    "attachment": [
                        {
                            "name": "invite.ics", 
                            "content": encoded_ics
                        }
                    ]
                }

                response = requests.post(url, json=payload, headers=headers)
                
                if response.status_code in [200, 201, 202]:
                     print(f"Sent email via API to {user.email}")
                     return jsonify({'message': 'Calendar invite sent to ' + user.email})
                else:
                     print(f"API Error: {response.text}")
                     return jsonify({'error': f'Failed to send email via API: {response.text}'}), 500
            except Exception as api_err:
                 print(f"API Exception: {api_err}")
                 return jsonify({'error': f'Failed to send email via API: {str(api_err)}'}), 500

        elif server_conf and username_conf and password_conf:
             try:
                 with smtplib.SMTP(server_conf, port_conf) as server:
                    if current_app.config.get('MAIL_USE_TLS'):
                        server.starttls()
                    server.login(username_conf, password_conf)
                    server.send_message(msg)
                 print(f"Sent email to {user.email}")
                 return jsonify({'message': 'Calendar invite sent to ' + user.email})
             except Exception as smtp_err:
                 print(f"SMTP Error: {smtp_err}")
                 if "111" in str(smtp_err) or "Connection refused" in str(smtp_err):
                     return jsonify({'error': 'Failed to send email: Connection refused (PythonAnywhere free tier blocks SMTP port 587). Please configure MAIL_API_KEY to use HTTP API.'}), 500
                 return jsonify({'error': f'Failed to send email: {str(smtp_err)}'}), 500
        else:
            print("--- EMAIL (MOCK - MISSING CONFIG) ---")
            print(f"To: {user.email}")
            print(f"Subject: {msg['Subject']}")
            return jsonify({'message': 'Calendar invite generated (but email config missing)'})
        
    except Exception as e:
        print(f"Error sending invite: {e}")
        return jsonify({'error': f'Failed to send invite: {str(e)}'}), 500

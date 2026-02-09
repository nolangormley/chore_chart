from flask import Blueprint, jsonify, request, url_for
from flask_login import login_required
from app.models import User
from app.extensions import db
from werkzeug.utils import secure_filename
import os

users_bp = Blueprint('users', __name__)

@users_bp.route('/api/users', methods=['GET', 'POST'])
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

@users_bp.route('/api/users/<int:user_id>', methods=['GET'])
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

@users_bp.route('/api/users/<int:user_id>', methods=['PUT'])
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

@users_bp.route('/api/users/<int:user_id>/upload-picture', methods=['POST'])
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
        # Assuming app.config['UPLOAD_FOLDER'] is globally available or we need to access via current_app
        from flask import current_app
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        user.profile_picture = url_for('static', filename=f'uploads/{filename}')
        db.session.commit()
        return jsonify({'message': 'File uploaded', 'url': user.profile_picture})

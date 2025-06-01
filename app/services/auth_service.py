from app.models.user import User
from flask_jwt_extended import create_access_token, create_refresh_token
from flask import current_app
from werkzeug.utils import secure_filename
import os
from datetime import datetime

class AuthService:
    @staticmethod
    def register(data, file=None):
        if User.objects(email=data['email']).first():
            return None, 'Email already exists'

        user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data.get('role', 'user')
        )
        user.set_password(data['password'])

        if file:
            filename = secure_filename(file.filename)
            if '.' in filename and \
                filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                user.profile_picture = file_path
            else:
                return None, 'Invalid image format'

        user.save()
        return user, None

    @staticmethod
    def authenticate(email, password):
        user = User.objects(email=email).first()
        print(f"Authenticating user: {email}")
        if user and user.check_password(password):
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            return access_token, refresh_token, user
        return None, None, None
    
    @staticmethod
    def update_profile(user_id, data):
        user = User.objects(id=user_id).first()
        if not user:
            return None, "User not found"
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.updated_at = datetime.utcnow()
        user.save()
        return user, None

    @staticmethod
    def change_password(user_id, old_password, new_password):
        user = User.objects(id=user_id).first()
        if not user or not user.check_password(old_password):
            return False, "Incorrect current password"
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        user.save()
        return True, None

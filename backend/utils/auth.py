from flask_jwt_extended import create_access_token, get_jwt_identity
from datetime import datetime
from models.user import User, db

class Auth:
    @staticmethod
    def create_user(username, password, role='user'):
        hashed_password = User.hash_password(password)
        user = User(username=username, password=hashed_password, role=role)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def authenticate_user(username, password):
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            return user
        return None

    @staticmethod
    def create_token(user):
        return create_access_token(identity={
            'id': user.id,
            'username': user.username,
            'role': user.role
        })

    @staticmethod
    def get_current_user():
        current_user = get_jwt_identity()
        if current_user:
            return User.query.get(current_user['id'])
        return None 
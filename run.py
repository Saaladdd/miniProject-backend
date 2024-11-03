from app import app, db, routes
from flask import request, jsonify
from app import models
from app.models import User, Restaurant, Menu, Dish, Theme, Preferences
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.functions import sort_user_preferences


if __name__ == "__main__":
    
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)

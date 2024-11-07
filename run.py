from myapp import db,app
from flask import request, jsonify
from myapp import models
from myapp.models import User, Restaurant, Menu, Dish, Theme, Preferences
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from myapp.functions import sort_user_preferences
from sqlalchemy import text


if __name__ == "__main__":
    with app.app_context():
        
        with db.engine.connect() as connection:
            connection.execute(text("PRAGMA foreign_keys = ON"))
        db.create_all()
    app.run(debug=True)

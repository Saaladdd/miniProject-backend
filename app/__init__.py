from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from datetime import timedelta


app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///DB.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'Num3R0n4u7s!Num3R0n4u7s!'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=6)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

from app import models

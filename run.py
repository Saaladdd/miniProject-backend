from app import app,db,migrate,jwt
from flask import request,jsonify
from app.models import User,Restaurant,Menu,Dish
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity



with app.app_context():
    db.create_all()



@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    preferences = data.get('preferences')

    if not email and not phone:
        return jsonify({"message": "Please enter your email or phone number."}), 401

    user_exists = User.query.filter((User.phonenumber == phone) | (User.email == email)).first()
    if user_exists:
        return jsonify({"message": "User with that username or email already exists"}), 400
    print(password)
    hashed_password = generate_password_hash(password)
    user = User(name=name,email=email,phone=phone, password=hashed_password,preferences=preferences)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    phone = data.get('phone')
    email = data.get('email')
    password = data.get('password')
    if phone:
        user = User.query.filter_by(phone=phone).first()

    elif email:
        user = User.query.filter_by(email=email).first()

    else:
        return jsonify({"message": "Please enter your email or phone number."}), 401

    if not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid credentials or password"}), 401

    access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=1))
    return jsonify(access_token=access_token), 200

@app.route('/api/add_restaurant',methods=['POST'])
def add_restaurant():
    data = request.json
    name = data.get('name')
    address = data.get('address')
    phone = data.get('phone')
    email = data.get('email')
    cuisine = data.get('cuisine')
    is_vegetarian = data.get('is_vegetarian')
    is_vegan = data.get('is_vegan')
    is_halal = data.get('is_halal')
    description = data.get('description')
    
    if not name or not phone or not email or not cuisine or not address:
        return jsonify({"message": "Please enter all required fields"}), 401

    new_restaurant = Restaurant(name=name, address=address, phone=phone, email=email, cuisine=cuisine, is_vegetarian=is_vegetarian, is_vegan=is_vegan, is_halal=is_halal, description=description)
    db.session.add(new_restaurant)
    db.session.commit()
    return jsonify({"message": "Restaurant added successfully"}), 201


@app.route('api/<int:rest_id>/create_menu',methods=['POST'])
def create_menu(rest_id):
    data = request.json
    menu_type = data.get('menu_type')
    if not menu_type:
        return jsonify({"message": "Please provide menu type."}), 401
    new_menu = Menu(menu_type=menu_type, restaurant_id=rest_id)
    db.session.add(new_menu)
    db.session.commit()
    return jsonify({"message": "Menu created successfully"}), 201

@app.route('/api/<int:rest_id>/get_menu',methods=['GET'])
def get_menu(rest_id):
    menu = Menu.query.filter_by(restaurant_id=rest_id).first()
    if not menu:
        return jsonify({"message": "Menu not found"}), 404
    return jsonify({"menu": menu.to_dict()})

@app.route('/api/<int:rest_id>/create_dish',methods=['POST'])
    
    













@app.route('/api/<int:user_id>/<int:rest_id>/menu', methods=['GET'])
def get_menu(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    


if __name__ == '__main__':
    app.run(debug=True)
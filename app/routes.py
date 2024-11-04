from flask import jsonify, request
import os
from app import app, db,jwt
from app.models import User, Preferences, Restaurant, Menu, Dish
from ai import create_user_description,chatbot_chat
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from flask_jwt_extended import JWTManager
from app.functions import sort_user_preferences
from openai import OpenAIError
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


@app.route('/api/user/register', methods=['POST'])
def register_user():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    preference = data.get('preference')
    password = data.get('password')
    phone = data.get('phone')
    is_lactose_intolerant = data.get('is_lactose_intolerant')
    is_halal = data.get('is_halal')
    is_vegan = data.get('is_vegan')
    is_vegetarian = data.get('is_vegetarian')
    is_allergic_to_gluten = data.get('is_allergic_to_gluten')
    is_jain = data.get('is_jain')

    if not email and not phone:
        return jsonify({"message": "Please enter your email or phone number."}), 401

    user_exists = User.query.filter((User.phone == phone) | (User.email == email)).first()
    if user_exists:
        return jsonify({"message": "User with that username or email already exists"}), 409
    print(password)
    hashed_password = generate_password_hash(password)
    user = User(name=name, email=email, phone=phone, password=hashed_password)
    try:
        db.session.add(user)
        db.session.flush()
        preferences = Preferences(
            user_id=user.id,
            preference=preference,
            is_lactose_intolerant=is_lactose_intolerant,
            is_halal=is_halal,
            is_vegan=is_vegan,
            is_vegetarian=is_vegetarian,
            is_allergic_to_gluten=is_allergic_to_gluten,
            is_jain=is_jain
        )
        db.session.add(preferences)
        try:user.user_description = create_user_description(user.id,app.config['OPENAI_API_KEY'])
        except OpenAIError as e:return jsonify({"error": str(e)}), 500
        db.session.add(user)
        db.session.commit()
        
        return jsonify({"message": "User and preferences created successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": e}), 500
 
@app.route('/api/user/login', methods=['POST'])
def login_user():
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

    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid credentials or password"}), 401

    access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=1))
    return jsonify(access_token=access_token), 200

@app.route('/api/user/delete/<int:user_id>', methods=['DELETE'])
@jwt_required
def delete_user(user_id):
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return jsonify({"message": "Unauthorized action."}), 403
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": e}), 500

@app.route('/api/restaurant/register',methods=['POST'])
def register_restaurant():
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
    password = data.get('password')
    
    if not name or not phone or not email or not cuisine or not address:
        return jsonify({"message": "Please enter all required fields"}), 401

    new_restaurant = Restaurant(name=name,password=password, address=address, phone=phone, email=email, cuisine=cuisine, is_vegetarian=is_vegetarian, is_vegan=is_vegan, is_halal=is_halal, description=description)
    db.session.add(new_restaurant)
    db.session.commit()
    return jsonify({"message": "Restaurant added successfully"}), 201

@app.route('/api/restaurant/login',methods=['POST'])
def login_restaurant():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({"message": "Please enter all required fields"}), 401
    restaurant = Restaurant.query.filter_by(email=email).first()
    if not restaurant or not check_password_hash(restaurant.password, password):
        return jsonify({"message": "Invalid credentials"}), 401
    access_token = create_access_token(identity=restaurant.id, expires_delta=timedelta(hours=1))
    return jsonify(access_token=access_token), 200

@app.route('/api/restaurant/delete/<int:rest_id>', methods=['DELETE'])
@jwt_required
def delete_restaurant(rest_id):
    current_rest_id = get_jwt_identity()
    if current_rest_id != rest_id:
        return jsonify({"message": "Unauthorized action."}), 403
    restaurant = Restaurant.query.get(rest_id)
    if not restaurant:
        return jsonify({"message": "Restaurant not found"}), 404
    try:
        db.session.delete(restaurant)
        db.session.commit()
        return jsonify({"message": "Restaurant deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": e}), 500

@app.route('/api/<int:rest_id>/create_menu',methods=['POST'])
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
def get_menus(rest_id):
    menu = Menu.query.filter_by(restaurant_id=rest_id).all()
    if not menu:
        return jsonify({"message": "Menu not found"}), 404
    return jsonify({"menu": [m.to_dict() for m in menu]})

@app.route('/api/<int:rest_id>/menu/delete/<int:menu_id>', methods=['DELETE'])
@jwt_required
def delete_menu(menu_id,rest_id):
    current_rest_id = get_jwt_identity()
    if current_rest_id != rest_id:
        return jsonify({"message": "Unauthorized action."}), 403
    menu = Menu.query.get(menu_id)
    if not menu:
        return jsonify({"message": "Menu not found"}), 404
    try:
        db.session.delete(menu)
        db.session.commit()
        return jsonify({"message": "Menu deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({"message": "Error deleting menu"}),500
    
@app.route('/api/<int:rest_id>/create_dish',methods=['POST'])
def create_dish(rest_id):
    data = request.json
    dish_name = data.get('dish_name')
    general_description = data.get('general_description')
    price = data.get('price')
    protein = data.get('protein')
    fat = data.get('fat')
    energy = data.get('energy')
    carbs = data.get('carbs')
    is_lactose_free = data.get('is_lactose_free')
    is_halal = data.get('is_halal')
    is_vegan = data.get('is_vegan')
    is_vegetarian = data.get('is_vegetarian')
    is_gluten_free = data.get('is_gluten_free')
    is_jain = data.get('is_jain')
    is_soy_free = data.get('is_soy_free')
    new_dish = Dish(
        dish_name=dish_name,
        description=general_description,
        price=price,
        protein=protein,
        fat=fat,
        energy=energy,
        carbs=carbs,
        is_lactose_free=is_lactose_free,
        is_halal=is_halal,
        is_vegan=is_vegan,
        is_vegetarian=is_vegetarian,
        is_gluten_free=is_gluten_free,
        is_jain=is_jain,
        is_soy_free=is_soy_free,
        restaurant_id=rest_id)
    try:
        db.session.add(new_dish)
        db.session.commit()
        return jsonify({"message": "Dish created successfully"}), 201
    except Exception as e:
        print(e)
        return jsonify({"message": "Error creating dish please ensure all required fields are filled."}), 500
    
@app.route('/api/<int:rest_id>/get_all_dishes',methods=['GET'])
def get_dishes(rest_id):
    dishes = Dish.query.filter_by(restaurant_id=rest_id).all()
    if not dishes:
        return jsonify({"message": "Dishes not found"}), 404
    return jsonify({"dishes": [dish.to_dict() for dish in dishes]})

@app.route('/api/add_to_menu',methods=['POST'])
def add_to_menu():
    data = request.json
    dish_id = data.get('dish_id')
    menu_id = data.get('menu_id')
    if not dish_id or not menu_id:
        return jsonify({"message": "Please provide dish_id and menu_id"}), 400
    dish = Dish.query.get(dish_id)
    if not dish:
        return jsonify({"message": "Dish not found"}), 404
    menu = Menu.query.get(menu_id)
    if not menu:
        return jsonify({"message": "Menu not found"}), 404
    if dish.menu_id == menu_id:
        return jsonify({"message": "Dish is already in the specified menu"}), 400
    try:
        dish.menu_id = menu_id  
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({"message": "Error adding dish to menu"}), 500
    return jsonify({"message": "Dish added to menu"}), 200

@app.route('/api/<int:rest_id>/get_menu/<int:menu_id>',methods=['GET'])
def get_restaurant_menu(rest_id,menu_id):
    menu = Menu.query.filter_by(restaurant_id=rest_id, id=menu_id).first()
    if not menu:
        return jsonify({"message": "Menu not found"}), 404
    return jsonify({"menu": menu.to_dict()})

@app.route('/api/<int:user_id>/menu/<int:menu_id>', methods=['GET'])
def get_user_menu(user_id, menu_id):
    user = User.query.get(user_id)
    choice = request.json.get('choice',0)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    menu = Menu.query.filter_by(id=menu_id).first()
    if not menu:
        return jsonify({"message": "Menu not found"}), 404
    
    all_dishes = {"dishes": [dish.to_dict() for dish in menu.dishes]}
    sorted_dishes = sort_user_preferences(user_id, menu_id)
    if choice == 1:
        return jsonify(all_dishes)
    else:
        return jsonify({"dishes": [dish.to_dict() for dish in sorted_dishes]})
    
    






    













@app.route('/api/<int:user_id>/<int:menu_id>', methods=['GET'])
def get_menu(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
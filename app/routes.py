from flask import jsonify, request, json, send_file
import os
from app import app, db
from app.models import User, Preferences, Restaurant, Menu, Dish, Theme, Order, OrderItem, Conversation, Favorites, Conversation
from ai import create_user_description,chatbot_chat
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager, get_jwt
from datetime import timedelta
from app.functions import sort_user_preferences, generate_session_id,hash_filename,generate_random_string,return_link
from openai import OpenAIError
from dotenv import load_dotenv
import openai
import random
import string

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/uploads/<path:filename>')
def serve_image(filename):
    try:
        filename = filename.replace('/','\\')
        return send_file("..\\"+filename)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/user/register', methods=['POST'])
def register_user():
    profile_photo = request.files.get('profile_photo')
    json_data = request.form.get('json_data')
    if json_data:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format"}), 400

    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    preference = data.get('preference')
    is_lactose_intolerant = data.get('is_lactose_intolerant')
    is_halal = data.get('is_halal')
    is_vegan = data.get('is_vegan')
    is_vegetarian = data.get('is_vegetarian')
    is_allergic_to_gluten = data.get('is_allergic_to_gluten')
    is_jain = data.get('is_jain')
    image_path = None

    if not email and not phone:
        return jsonify({'message': 'Please enter your email or phone number.'}), 401

    user_exists = User.query.filter((User.phone == phone) | (User.email == email)).first()
    if user_exists:
        return jsonify({'message': 'User with that username or email already exists.'}), 409
    
    
    hashed_password = generate_password_hash(password)
    user = User(
        name=name,
        email=email,
        phone=phone,
        password=hashed_password,
        profile_photo = image_path
    )

    try:
        with db.session.no_autoflush:
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

        try:
            user.user_description = create_user_description(user.id, app.config['OPENAI_API_KEY'])
        except OpenAIError as e:
            return jsonify({'error': str(e)}), 500

        db.session.add(user)
        db.session.commit()
        if profile_photo:
            ext = profile_photo.filename.split('.')[-1]
            unique_filename = f"{generate_random_string(16)}.{ext}"
            image_path = os.path.join(app.config['USER_PROFILE_PICTURE_PATH'], unique_filename)
            os.makedirs(app.config['USER_PROFILE_PICTURE_PATH'], exist_ok=True)
            profile_photo.save(image_path)
        
        user.profile_photo = image_path
        db.session.commit()
        return jsonify({'message': 'User and preferences created successfully.'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500
    
@app.route('/api/role', methods=['GET'])
@jwt_required()
def get_user_role():
    jwt_claims = get_jwt()
    role = jwt_claims.get('role', 'user')
    return jsonify({'role': role}), 200

@app.route('/api/user/get', methods=['GET'])
@jwt_required()
def get_user():
    user_id = get_jwt_identity()
    try:
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404

        
        preferences = Preferences.query.filter_by(user_id=user_id).first()
        preferences_data = {
            "is_lactose_intolerant": preferences.is_lactose_intolerant if preferences else None,
            "is_halal": preferences.is_halal if preferences else None,
            "is_vegan": preferences.is_vegan if preferences else None,
            "is_vegetarian": preferences.is_vegetarian if preferences else None,
            "is_allergic_to_gluten": preferences.is_allergic_to_gluten if preferences else None,
            "is_jain": preferences.is_jain if preferences else None,
        }

        other_preferences_data = {
            "preference": preferences.preference if preferences else None,
        }
        
        orders = user.orders[-5:]
        orders_data = [
            {
                "id": order.id,
                "restaurant_id": order.restaurant_id,
                "restaurant_name": Restaurant.query.get(order.restaurant_id).name,
                "total_cost": order.total_cost,
                "timestamp": order.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }
            for order in orders
        ]

        
        favorite_restaurants = [
            {
                "id": fav.restaurant_id,
                "name": Restaurant.query.get(fav.restaurant_id).name
            }
            for fav in Favorites.query.filter_by(user_id=user_id).all()
        ]
        favorite_dishes = [
            {
                "id": dish.id,
                "name": dish.dish_name
            }
            for dish in Dish.query.filter(Dish.favorites_id.in_(
                [fav.id for fav in Favorites.query.filter_by(user_id=user_id).all()]
            )).all()
        ]


        conversations = Conversation.query.filter_by(user_id=user_id).order_by(Conversation.created_at.desc()).limit(5).all()
        conversations_data = [
            {
                "id": convo.id,
                "rest_id": convo.rest_id,
                "restaurant_name": Restaurant.query.get(convo.rest_id).name,
                "content": convo.content,
                "created_at": convo.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for convo in conversations
        ]

        response = {
            "user": user.to_dict(),
            "preferences": preferences_data,
            "other_preferences": other_preferences_data,
            "orders": orders_data,
            "favorites": {
                "restaurants": favorite_restaurants,
                "dishes": favorite_dishes,
            },
            "conversations": conversations_data,
        }
        response["user"]["profile_photo"] = return_link(user.profile_photo)

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500

    

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

    access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=2), additional_claims={"role": "user"})
    return jsonify(access_token=access_token), 200

@app.route('/api/user/edit',methods=['POST'])
@jwt_required()
def edit_user():
    user_id = get_jwt_identity()
    json_data = request.form.get('json_data')
    if json_data:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format"}), 400
    else:
        data = {}

    
    name = data.get('name')
    email = data.get('email')
    preference = data.get('preference')
    phone = data.get('phone')
    profile_photo = request.files.get('profile_photo')
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    user_pref = Preferences.query.filter_by(user_id=user_id).first()
    if not user_pref:
        return jsonify({'message': 'Preferences not found'}), 404
    image_path = user.profile_photo
    if profile_photo:
        old_photo_filename = user.profile_photo
        if old_photo_filename:
                os.remove(old_photo_filename)
        ext = profile_photo.filename.split('.')[-1]
        unique_filename = f"{generate_random_string(16)}.{ext}"
        image_path = os.path.join(app.config['USER_PROFILE_PICTURE_PATH'], unique_filename)
        os.makedirs(app.config['USER_PROFILE_PICTURE_PATH'], exist_ok=True)
        profile_photo.save(image_path)
    is_lactose_intolerant = data.get('is_lactose_intolerant')
    is_halal = data.get('is_halal')
    is_vegan = data.get('is_vegan')
    is_vegetarian = data.get('is_vegetarian')
    is_allergic_to_gluten = data.get('is_allergic_to_gluten')
    is_jain = data.get('is_jain')
    existing_user_by_phone = User.query.filter(User.phone == phone, User.id != user_id).first()
    existing_user_by_email = User.query.filter(User.email == email, User.id != user_id).first()

    if existing_user_by_phone or existing_user_by_email:
        return jsonify({"message": "User with that phone number or email already exists"}), 409
    try:
        user.name = name or user.name
        user.email = email or user.email
        user.phone = phone or user.phone
        user.profile_photo = image_path
        user_pref.preference = preference or user_pref.preference
        user_pref.is_lactose_intolerant = is_lactose_intolerant or user_pref.is_lactose_intolerant
        user_pref.is_halal = is_halal or user_pref.is_halal
        user_pref.is_vegan = is_vegan or user_pref.is_vegan
        user_pref.is_vegetarian = is_vegetarian or user_pref.is_vegetarian
        user_pref.is_allergic_to_gluten = is_allergic_to_gluten or user_pref.is_allergic_to_gluten
        user_pref.is_jain = is_jain or user_pref.is_jain
        if preference or is_lactose_intolerant or is_halal or is_vegan or is_vegetarian or is_allergic_to_gluten or is_jain:
            user.user_description = create_user_description(user.id,app.config['OPENAI_API_KEY'])
        db.session.commit()
        return jsonify({"message": "User updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@app.route('/api/user/delete', methods=['DELETE'])
@jwt_required()
def delete_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    try:
        if user.profile_photo:
            old_photo_filename = user.profile_photo
            if old_photo_filename:
                old_image_path = os.path.join(app.config['USER_PROFILE_PICTURE_PATH'], old_photo_filename)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@app.route('/api/restaurant/register',methods=['POST'])
def register_restaurant():
    json_data = request.form.get('json_data')
    if json_data:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format"}), 400
    else:
        return jsonify({"error": "No JSON data provided"}), 400
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
    banner = request.files.get('banner')
    profile_picture = request.files.get('profile_picture')
    banner_path = None
    profile_picture_path = None

    if banner:
        unique_filename = hash_filename(banner)
        banner_path = os.path.join(app.config['RESTAURANT_BANNER_PATH'], unique_filename)
        os.makedirs(app.config['RESTAURANT_BANNER_PATH'], exist_ok=True)
        banner.save(banner_path)
    if profile_picture:
        unique_filename = hash_filename(profile_picture)
        profile_picture_path = os.path.join(app.config['RESTAURANT_PROFILE_PICTURE_PATH'], unique_filename)
        os.makedirs(app.config['RESTAURANT_PROFILE_PICTURE_PATH'], exist_ok=True)
        profile_picture.save(profile_picture_path)
    
    if not name or not phone or not email or not cuisine or not address:
        return jsonify({"message": "Please enter all required fields"}), 401
    
    if (Restaurant.query.filter_by(phone=phone).all()) or (Restaurant.query.filter_by(email=email)).all():
        return jsonify({"message": "Restaurant with that phone number or email already exists"}), 409

    new_restaurant = Restaurant(name=name,password=generate_password_hash(password),
                                address=address, phone=phone, email=email, cuisine=cuisine,
                                is_vegetarian=is_vegetarian, is_vegan=is_vegan, is_halal=is_halal, 
                                description=description, banner=banner_path, profile_photo=profile_picture_path)
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
    access_token = create_access_token(identity=restaurant.id, expires_delta=timedelta(hours=1), additional_claims={"role": "restaurant"})
    return jsonify(access_token=access_token), 200

@app.route('/api/restaurant/edit',methods=['POST'])
@jwt_required()
def edit_restaurant():
    rest_id = get_jwt_identity()
    restaurant = Restaurant.query.get(rest_id)
    if not restaurant:
        return jsonify({"message": "Restaurant not found"}), 404
    
    json_data = request.form.get('json_data')
    if json_data:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format"}), 400
    else:
        data = {}
    
    name = data.get('name')
    address = data.get('address')
    phone = data.get('phone')
    email = data.get('email')
    cuisine = data.get('cuisine')
    is_vegetarian = data.get('is_vegetarian')
    is_vegan = data.get('is_vegan')
    is_halal = data.get('is_halal')
    description = data.get('description')
    banner = request.files.get('banner')
    profile_picture = request.files.get('profile_picture')
    banner_path = None
    profile_picture_path = None

    if banner:
        old_banner = restaurant.banner
        if old_banner:
            os.remove(old_banner)
        unique_filename = hash_filename(banner)
        banner_path = os.path.join(app.config['RESTAURANT_BANNER_PATH'], unique_filename)
        os.makedirs(app.config['RESTAURANT_BANNER_PATH'], exist_ok=True)
        banner.save(banner_path)
    if profile_picture:
        old_profile_picture = restaurant.profile_picture
        if old_profile_picture:
            os.remove(old_profile_picture)
        unique_filename = hash_filename(profile_picture)
        profile_picture_path = os.path.join(app.config['RESTAURANT_PROFILE_PICTURE_PATH'], unique_filename)
        os.makedirs(app.config['RESTAURANT_PROFILE_PICTURE_PATH'], exist_ok=True)
        profile_picture.save(profile_picture_path)
    
    if phone == Restaurant.query.filter_by(phone).first() or email == Restaurant.query.filter_by(email).first():
        return jsonify({"message":"Restaurant with that phone or email already exists."}),409


    try:
        restaurant.name = name or restaurant.name
        restaurant.address = address or restaurant.address
        restaurant.phone = phone or restaurant.phone
        restaurant.email = email or restaurant.email
        restaurant.cuisine = cuisine or restaurant.cuisine
        restaurant.is_vegetarian = is_vegetarian or restaurant.is_vegetarian
        restaurant.is_vegan = is_vegan or restaurant.is_vegan
        restaurant.is_halal = is_halal or restaurant.is_halal
        restaurant.description = description or restaurant.description
        restaurant.banner = banner_path or restaurant.banner
        restaurant.profile_picture = profile_picture_path or restaurant.profile_picture
        db.session.commit()
        return jsonify({"message": "Restaurant updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500
    
@app.route('/api/restaurant/landing/<int:rest_id>',methods=['GET'])
def get_restaurant():
    rest_id = get_jwt_identity()
    restaurant = Restaurant.query.get(rest_id)
    if not restaurant:
        return jsonify({"message": "Restaurant not found"}), 404
    return jsonify(restaurant.to_dict()), 200

@app.route('/api/restaurant/delete', methods=['DELETE'])
@jwt_required()
def delete_restaurant(rest_id):
    current_rest_id = get_jwt_identity()
    if current_rest_id != rest_id:
        return jsonify({"message": "Unauthorized action."}), 403
    restaurant = Restaurant.query.get(rest_id)
    if not restaurant:
        return jsonify({"message": "Restaurant not found"}), 404
    try:
        if restaurant.banner:
            os.remove(restaurant.banner)
        if restaurant.profile_picture:
            os.remove(restaurant.profile_picture)
        db.session.delete(restaurant)
        db.session.commit()
        return jsonify({"message": "Restaurant deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": e}), 500


@app.route('/api/create_menu',methods=['POST'])
@jwt_required()
def create_menu():
    rest_id = get_jwt_identity()
    data = request.json
    menu_type = data.get('menu_type')
    if not menu_type:
        return jsonify({"message": "Please provide menu type."}), 401
    new_menu = Menu(menu_type=menu_type, restaurant_id=rest_id)
    db.session.add(new_menu)
    db.session.commit()
    return jsonify({"message": "Menu created successfully"}), 201

@app.route('/api/get_menu',methods=['GET'])
@jwt_required()
def get_menus():
    rest_id = get_jwt_identity()
    menu = Menu.query.filter_by(restaurant_id=rest_id).all()
    if not menu:
        return jsonify({"message": "Menu not found"}), 404
    return jsonify({"menu": [m.to_dict() for m in menu]})

@app.route('/api/menu/delete/<int:menu_id>', methods=['DELETE'])
@jwt_required()
def delete_menu(menu_id):
    rest_id = get_jwt_identity()
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
    
@app.route('/api/create_dish',methods=['POST'])
@jwt_required()
def create_dish():
    rest_id = get_jwt_identity()
    json_data = request.form.get('json_data')
    if json_data:
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format"}), 400
    else:
        return jsonify({"error": "No JSON data provided"}), 400
    
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
    image = request.files.get('image')
    image_path = None
    if image:
        unique_filename = f"{rest_id}{dish_name}_{image.filename}"
        image_path = os.path.join(app.config['DISH_IMAGE_PATH'], unique_filename)
        os.makedirs(app.config['DISH_IMAGE_PATH'], exist_ok=True)
        image.save(image_path)

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
        restaurant_id=rest_id,
        image=image_path)
    try:
        db.session.add(new_dish)
        db.session.commit()
        return jsonify({"message": "Dish created successfully"}), 201
    except Exception as e:
        print(e)
        return jsonify({"message": "Error creating dish please ensure all required fields are filled."}), 500

@app.route('/api/get_all_dishes',methods=['GET'])
@jwt_required()
def get_dishes(rest_id):
    rest_id = get_jwt_identity()
    dishes = Dish.query.filter_by(restaurant_id=rest_id).all()
    if not dishes:
        return jsonify({"message": "Dishes not found"}), 404
    dishes = [dish.to_dict() for dish in dishes]
    for dish in dishes:
        dish['image'] = return_link(dish.image)
    return jsonify({"dishes": dishes })


@app.route('/api/dish/<int:dish_id>', methods=['GET'])
def get_dish(dish_id):
    dish = Dish.query.get(dish_id)
    if not dish:
        return jsonify({"message": "Dish not found"}), 404
    dishes = dish.image_and_name()
    dishes['image'] = return_link(dish.image)
    return jsonify({"dishes":dishes}), 200

@app.route('/api/add_to_menu',methods=['POST'])
@jwt_required()
def add_to_menu():
    rest_id = get_jwt_identity()
    data = request.json
    dish_id = data.get('dish_id')
    menu_id = data.get('menu_id')
    if not dish_id or not menu_id:
        return jsonify({"message": "Please provide dish_id and menu_id"}), 400
    dish = Dish.query.get(dish_id)
    if not dish:
        return jsonify({"message": "Dish not found"}), 404
    menu = Menu.query.get(menu_id)
    if not menu or menu.restaurant_id != rest_id:
        return jsonify({"message": "Menu not found or unauthorized"}), 404
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

@app.route('/api/get_menu/<int:menu_id>',methods=['GET'])
@jwt_required()
def get_restaurant_menu(menu_id):
    rest_id = get_jwt_identity()
    menu = Menu.query.filter_by(restaurant_id=rest_id, id=menu_id).first()
    if not menu:
        return jsonify({"message": "Menu not found"}), 404
    return jsonify({"menu": menu.to_dict()})

@app.route('/api/user_menu/<int:menu_id>', methods=['GET'])
def get_user_menu( menu_id):
    user_id = get_jwt_identity()
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

@app.route('/api/start_order/<int:rest_id>', methods=['POST'])
@jwt_required()
def start_order(rest_id):
    user_id = get_jwt_identity()
    session_id = generate_session_id(user_id)
    user = User.query.get(user_id)
    existing_session = Order.query.filter_by(session_id=session_id).first()
    
    if not existing_session:
        try:
            for order in user.orders:
                order.status = False
                db.session.flush()
            new_order = Order(user_id=user_id, session_id=session_id, restaurant_id=rest_id, status=True)
            db.session.add(new_order)
            db.session.commit()
        except Exception as e: 
            db.session.rollback()
            print(e)
            return jsonify({"message": str(e)}), 500
        return jsonify(session_id=session_id)
    else:
        return jsonify({"message": "Try again"}), 400

@app.route('/api/<int:session_id>/order', methods=['POST'])
@jwt_required()
def create_order(session_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    active_order = next((order for order in user.orders if order.status == True), None)
    print(active_order)
    if not active_order or active_order.session_id != session_id:
        return jsonify({"message": "Invalid Session"}), 403
    data = request.json 
    items = data.get('items', [])
    if not items:
        return jsonify({"message": "No items provided"}), 400
    try:
        order = Order.query.filter_by(session_id=session_id).first()
        total_cost = order.total_cost
        if order.status == False:
            return jsonify({"message": "Invalid Session"}),403
        for item in items:
            dish_id = item.get('dish_id')
            quantity = item.get('quantity')
            
            if not all([dish_id, quantity]):
                return jsonify({"message": "Item data is incomplete"}), 400
            
            total_cost += (Dish.query.get(dish_id).price)*quantity
            order_item = OrderItem(order_id=order.id, dish_id=dish_id, quantity=quantity, price=(Dish.query.get(dish_id).price)*quantity)
            db.session.add(order_item)

        order.total_cost = total_cost 
        db.session.commit()
        return jsonify({"message": "Order created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error processing order", "error": str(e)}), 500
    
@app.route('/api/end_order/<int:session_id>', methods=['POST'])
@jwt_required()
def end_order(session_id):
    user_id = get_jwt_identity()
    order = Order.query.filter_by(session_id=session_id,user_id=user_id).first()
    if not order:
        return jsonify({"message": "Order not found"}), 404
    try:
        order.status = False
        db.session.commit()
        return jsonify({"message": "Order completed successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error processing order", "error": str(e)}), 500
    
@app.route('/api/chat/get/<int:rest_id>', methods=['GET'])
@jwt_required()
def get_chat(rest_id):
    user_id = get_jwt_identity()
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({"message": "Missing session_id"}), 400
    try:
        chats = Conversation.query.filter_by(session_id=session_id, user_id=user_id).all()
        if not chats:
            return jsonify({"message": "No chats found"}), 404
        chat_list = [chat.get_all_chats() for chat in chats]
    except Exception as e:
        return jsonify({"message": "Error processing chat", "error": str(e)}), 500

    return jsonify({"chats": chat_list}), 200
    
@app.route('/api/chat/<int:rest_id>', methods=['POST'])
@jwt_required()
def chat(rest_id):
    user_id = get_jwt_identity()
    data = request.json
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({"message": "Missing session_id"}), 400
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    data = request.get_json()
    user_input = data.get('user_input')
    try:
        try:
            chat_response_tuple = chatbot_chat(user_id, rest_id, user_input, session_id, app.config['OPENAI_API_KEY'])
            


            chat_response = chat_response_tuple[0]
            print(chat_response.get_json()) 

            chat_reply = chat_response.json.get("reply", "{}")
            chat_reply = json.loads(chat_reply)
    
        except Exception as e: 
            return jsonify({"message": "Error with chat", "error": str(e)}), 500

        if not isinstance(chat_reply, dict):
            return jsonify({"message": "Invalid reply format", "error": "Expected a dictionary"}), 400

        text = chat_reply.get('text', "")
        dishes = chat_reply.get('dishes', [])
        dish_ids = [dish.get("dish_id") for dish in dishes if "dish_id" in dish]
        queried_dishes = Dish.query.filter(Dish.id.in_(dish_ids)).all()
        dish_details = [
            {
                "dish_id": dish.id,
                **dish.image_and_name()
            }
            for dish in queried_dishes
]
        print(dish_details)
        return jsonify({"text": text, "dish_details": dish_details}), 200
    except Exception as e:
        return jsonify({"message": "Error processing chat", "error": str(e)}), 500


   





    













@app.route('/api/<int:user_id>/<int:menu_id>', methods=['GET'])
def get_menu(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
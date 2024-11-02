from app import app,db,migrate,jwt
from flask import request,jsonify
from app.models import User,Restaurant,Menu,Dish,Theme,Preferences
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

db.init_app(app)


@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    preference = data.get('preferences')
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
        db.session.commit()
        return jsonify({"message": "User and preferences created successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while creating the user and preferences"}), 500
 
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

    if not user or not check_password_hash(user.password, password):
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
def get_menu(rest_id):
    menu = Menu.query.filter_by(restaurant_id=rest_id).all()
    if not menu:
        return jsonify({"message": "Menu not found"}), 404
    return jsonify({"menu": [m.to_dict() for m in menu]})

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
    menu_id = data.get('menu_id')
    new_dish = Dish(
        dish_name=dish_name,
        general_description=general_description,
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
        menu_id=menu_id
    )
    try:
        db.session.add(new_dish)
        db.session.commit()
        return jsonify({"message": "Dish created successfully"}), 201
    except Exception as e:
        return jsonify({"message": "Error creating dish please ensure all required fields are filled."}), 500
    

@app.route('/api/<int:rest_id>/<int:menu_id>/get_dishes',methods=['GET'])
def get_dishes(rest_id,menu_id):
    dishes = Dish.query.filter_by(menu_id=menu_id).all()
    if not dishes:
        return jsonify({"message": "Dishes not found"}), 404
    return jsonify({"dishes": [dish.to_dict() for dish in dishes]})


    













@app.route('/api/<int:user_id>/<int:menu_id>', methods=['GET'])
def get_menu(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
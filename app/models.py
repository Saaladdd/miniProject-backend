from app import db

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    phone = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120), unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    preference = db.Column(db.String(120), unique=True, nullable=False)
    is_lactose_intolerant = db.Column(db.Boolean, default=False)
    is_halal = db.Column(db.Boolean, default=False)
    is_vegan = db.Column(db.Boolean, default=False)
    is_vegetarian = db.Column(db.Boolean, default=False)
    is_allergic_to_gluten = db.Column(db.Boolean, default=False)
    is_jain = db.Column(db.Boolean, default=False)

class Restaurant(db.Model):
    __tablename__ = 'restaurant'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(12), unique=True, nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    cuisine = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Integer)
    is_vegan = db.Column(db.Boolean, default=False)
    is_vegetarian = db.Column(db.Boolean, default=False)
    is_halal = db.Column(db.Boolean, default=False)
    description = db.Column(db.String(200))
    menus = db.relationship('Menu', backref='restaurant', lazy=True)

class Menu(db.Model):
    __tablename__ = 'menu'
    id = db.Column(db.Integer, primary_key=True)
    menu_type = db.Column(db.String(10), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    dishes = db.relationship('Dish', backref='menu', lazy=True)

class Dish(db.Model):
    __tablename__ = 'dish'
    id = db.Column(db.Integer, primary_key=True)
    dish_name = db.Column(db.String(100), nullable=False)
    general_description = db.Column(db.String(200))
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=False)
    description = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    energy = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False) 
    is_lactose_free = db.Column(db.Boolean, default=True)
    is_halal = db.Column(db.Boolean, default=True)
    is_vegan = db.Column(db.Boolean, default=True)
    is_vegetarian = db.Column(db.Boolean, default=True)
    is_gluten_free = db.Column(db.Boolean, default=True)
    is_jain = db.Column(db.Boolean, default=True)
    is_soy_free = db.Column(db.Boolean, default=True)
    is_available = db.Column(db.Boolean, default=True)
    #image

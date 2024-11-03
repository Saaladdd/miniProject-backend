from app import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(120), unique=True)
    email = db.Column(db.String(60), unique=True)
    preferences = db.relationship('Preferences', backref='user', lazy=True)

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}', phone='{self.phone}')>"

class Preferences(db.Model):
    __tablename__ = 'preferences'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    preference = db.Column(db.String(120), nullable=False)
    is_lactose_intolerant = db.Column(db.Boolean, default=False)
    is_halal = db.Column(db.Boolean, default=False)
    is_vegan = db.Column(db.Boolean, default=False)
    is_vegetarian = db.Column(db.Boolean, default=False)
    is_allergic_to_gluten = db.Column(db.Boolean, default=False)
    is_jain = db.Column(db.Boolean, default=False)
    favorites = db.Column(db.String(200))

    def __repr__(self):
        return (f"<Preferences(id={self.id}, user_id={self.user_id}, preference='{self.preference}', "
                f"is_lactose_intolerant={self.is_lactose_intolerant}, is_halal={self.is_halal}, "
                f"is_vegan={self.is_vegan}, is_vegetarian={self.is_vegetarian}, "
                f"is_allergic_to_gluten={self.is_allergic_to_gluten}, is_jain={self.is_jain})>")


class Restaurant(db.Model):
    __tablename__ = 'restaurant'
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(12), unique=True, nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    cuisine = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Float)
    is_vegan = db.Column(db.Boolean, default=False)
    is_vegetarian = db.Column(db.Boolean, default=False)
    is_halal = db.Column(db.Boolean, default=False)
    description = db.Column(db.String(200))
    menus = db.relationship('Menu', backref='restaurant', lazy=True)

    def __repr__(self):
        return (f"<Restaurant(id={self.id}, name='{self.name}', cuisine='{self.cuisine}', "
                f"address='{self.address}', phone='{self.phone}', email='{self.email}', "
                f"rating={self.rating})>")

class Favorites(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    dish = db.relationship('Dish', backref='favorites', lazy=True)

    def __repr__(self):
        return (f"<Favorites(id={self.id}, user_id={self.user_id}, restaurant_id={self.restaurant_id}, "
                f"category='{self.category}')>")
    
class Menu(db.Model):
    __tablename__ = 'menu'
    id = db.Column(db.Integer, primary_key=True)
    menu_type = db.Column(db.String(20), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    dishes = db.relationship('Dish', backref='menu', lazy=True)

    def __repr__(self):
        return f"<Menu(id={self.id}, menu_type='{self.menu_type}', restaurant_id={self.restaurant_id})>"

    def to_dict(self):
        return {
            "id": self.id,
            "menu_type": self.menu_type,
            "restaurant_id": self.restaurant_id,
            "dishes": [dish.to_dict() for dish in self.dishes]
        }

class Dish(db.Model):
    __tablename__ = 'dish'
    id = db.Column(db.Integer, primary_key=True)
    dish_name = db.Column(db.String(100), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id'))
    description = db.Column(db.String(200))
    price = db.Column(db.Float)
    protein = db.Column(db.Float)
    fat = db.Column(db.Float)
    energy = db.Column(db.Float)
    carbs = db.Column(db.Float)
    is_lactose_free = db.Column(db.Boolean, default=True)
    is_halal = db.Column(db.Boolean, default=True)
    is_vegan = db.Column(db.Boolean, default=True)
    is_vegetarian = db.Column(db.Boolean, default=True)
    is_gluten_free = db.Column(db.Boolean, default=True)
    is_jain = db.Column(db.Boolean, default=True)
    is_soy_free = db.Column(db.Boolean, default=True)
    is_available = db.Column(db.Boolean, default=True)
    image = db.Column(db.String(100))
    def __repr__(self):
        return (f"<Dish(id={self.id}, dish_name='{self.dish_name}', price={self.price}, "
                f"restaurant_id={self.restaurant_id}, menu_id={self.menu_id}, "
                f"is_available={self.is_available})>")

    def to_dict(self):
        return {
            "id": self.id,
            "dish_name": self.dish_name,
            "price": self.price,
            "protein": self.protein,
            "fat": self.fat,
            "energy": self.energy,
            "carbs": self.carbs,
            "is_lactose_free": self.is_lactose_free,
            "is_halal": self.is_halal,
            "is_vegan": self.is_vegan,
            "is_vegetarian": self.is_vegetarian,
            "is_gluten_free": self.is_gluten_free,
            "is_jain": self.is_jain,
            "is_soy_free": self.is_soy_free,
            "is_available": self.is_available,
            "image": self.image
        }

class Theme(db.Model):
    __tablename__ = 'theme'
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    bgcolor = db.Column(db.String(50))
    accentcolor1 = db.Column(db.String(50))
    accentcolor2 = db.Column(db.String(50))
    logo1 = db.Column(db.String(100))
    logo2 = db.Column(db.String(100))

    def __repr__(self):
        return (f"<Theme(id={self.id}, restaurant_id={self.restaurant_id}, "
                f"bgcolor='{self.bgcolor}', accentcolor1='{self.accentcolor1}', "
                f"accentcolor2='{self.accentcolor2}', logo1='{self.logo1}', logo2='{self.logo2}')>")
    
class Conversation(db.Model):
    __tablename__ = 'chat_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(50), nullable=False)
    user_description = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return (f"<ChatHistory(id={self.id}, user_id={self.user_id}, message='{self.content}', "
                f"created_at='{self.created_at}')>")
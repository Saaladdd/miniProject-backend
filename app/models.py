from app import db
from datetime import datetime
import pytz
ist = pytz.timezone('Asia/Kolkata')
def return_link(filename):
    return f"http://localhost:5000/uploads/{filename}"

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(120), unique=True)
    email = db.Column(db.String(60), unique=True)
    user_description = db.Column(db.String(200))
    profile_photo = db.Column(db.String(100))
    preferences = db.relationship('Preferences', backref='user', lazy=True, cascade="all, delete-orphan")
    orders = db.relationship('Order', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}', phone='{self.phone}')>"
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if (c.name != "password" and c.name != "id")}

class Preferences(db.Model):
    __tablename__ = 'preferences'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_preferences_user_id', ondelete='CASCADE'), nullable=False)
    preference = db.Column(db.String(120), nullable=False)
    is_lactose_intolerant = db.Column(db.Boolean, default=False)
    is_halal = db.Column(db.Boolean, default=False)
    is_vegan = db.Column(db.Boolean, default=False)
    is_vegetarian = db.Column(db.Boolean, default=False)
    is_allergic_to_gluten = db.Column(db.Boolean, default=False)
    is_jain = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return (f"<Preferences(id={self.id}, user_id={self.user_id}, preference='{self.preference}', "
                f"is_lactose_intolerant={self.is_lactose_intolerant}, is_halal={self.is_halal}, "
                f"is_vegan={self.is_vegan}, is_vegetarian={self.is_vegetarian}, "
                f"is_allergic_to_gluten={self.is_allergic_to_gluten}, is_jain={self.is_jain})>")

    def description(self):
        return (f"""is_lactose_intolerant={self.is_lactose_intolerant}, is_halal={self.is_halal},
                 is_vegan={self.is_vegan}, is_vegetarian={self.is_vegetarian},
                 is_allergic_to_gluten={self.is_allergic_to_gluten}, is_jain={self.is_jain},
                 preference='{self.preference}'
                 """)
    
class Restaurant(db.Model):
    __tablename__ = 'restaurant'
    id = db.Column(db.Integer, primary_key=True)
    banner = db.Column(db.String(100))
    profile_photo = db.Column(db.String(100))
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
    menus = db.relationship('Menu', backref='restaurant', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if (c.name != "password" and c.name != "id")}

    def __repr__(self):
        return (f"<Restaurant(id={self.id}, name='{self.name}', cuisine='{self.cuisine}', "
                f"address='{self.address}', phone='{self.phone}', email='{self.email}', "
                f"rating={self.rating})>")

class RestaurantReview(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_review_user_id', ondelete='CASCADE'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id', name='fk_review_restaurant_id', ondelete='CASCADE'), nullable=False)
    comment = db.Column(db.String(200), nullable=True)
    rating = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return (f"<Review(id={self.id}, user_id={self.user_id}, restaurant_id={self.restaurant_id}, "
                f"review='{self.review}', rating={self.rating})>")

class Favorites(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_favorites_user_id', ondelete='CASCADE'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id', name='fk_favorites_restaurant_id', ondelete='CASCADE'), nullable=False)
    category = db.Column(db.String(20), nullable=True)
    dish = db.relationship('Dish', backref='favorites', lazy=True)

    def __repr__(self):
        return (f"<Favorites(id={self.id}, user_id={self.user_id}, restaurant_id={self.restaurant_id}, "
                f"category='{self.category}')>")

class Menu(db.Model):
    __tablename__ = 'menu'
    id = db.Column(db.Integer, primary_key=True)
    menu_type = db.Column(db.String(20), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id', name='fk_menu_restaurant_id'), nullable=False)
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
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id', name='fk_dish_restaurant_id', ondelete='CASCADE'), nullable=False)
    favorites_id = db.Column(db.Integer, db.ForeignKey('favorites.id', ondelete='CASCADE'))
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id', name='fk_dish_menu_id'))
    description = db.Column(db.String(200))
    price = db.Column(db.Float)
    protein = db.Column(db.Float)
    fat = db.Column(db.Float)
    energy = db.Column(db.Float)
    carbs = db.Column(db.Float)
    is_lactose_free = db.Column(db.Boolean, default=False)
    is_halal = db.Column(db.Boolean, default=False)
    is_vegan = db.Column(db.Boolean, default=False)
    is_vegetarian = db.Column(db.Boolean, default=False)
    is_gluten_free = db.Column(db.Boolean, default=False)
    is_jain = db.Column(db.Boolean, default=False)
    is_soy_free = db.Column(db.Boolean, default=False)
    is_available = db.Column(db.Boolean, default=True)
    image = db.Column(db.String(100))
    rating = db.Column(db.Integer, default=5)
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
            "image": return_link(self.image)
        }
    
    def image_and_name(self):
        return {
            "image": self.image,
            "name": self.dish_name
        }
    
class Theme(db.Model):
    __tablename__ = 'theme'
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id', name='fk_theme_restaurant_id', ondelete='CASCADE'), nullable=False)
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
    __tablename__ = 'conversation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_chat_history_user_id', ondelete='CASCADE'), nullable=False)
    rest_id = db.Column(db.Integer, db.ForeignKey('restaurant.id', name='fk_chat_history_rest_id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(50), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('orders.session_id', name='fk_chat_history_session_id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(ist))
    dish_ids = db.Column(db.PickleType, nullable=True)
    def __repr__(self):
        return (f"<ChatHistory(id={self.id}, user_id={self.user_id}, message='{self.content}', "
                f"created_at='{self.created_at}')>")
    
    def get_all_chats(self):
        return {
            "role": self.role,
            "message": self.content,
            "created_at": self.created_at
        }

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_orders_user_id', ondelete='CASCADE'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id', name='fk_orders_restaurant_id', ondelete='CASCADE'), nullable=False)
    session_id = db.Column(db.Integer, nullable=False, unique=True)
    status = db.Column(db.Boolean, nullable=False)
    order_status = db.Column(db.Integer)
    total_cost = db.Column(db.Float, default=0.0)
    timestamp = db.Column(db.DateTime, default=datetime.now(ist))
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return (f"Order(id={self.id}, user_id={self.user_id}, restaurant_id={self.restaurant_id}, "
                f"session_id={self.session_id}, status={self.status}, total_cost={self.total_cost}, "
                f"timestamp={self.timestamp})")
    
    def get_status(self):
        return self.status

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'restaurant_id': self.restaurant_id,
            'session_id': self.session_id,
            'status': self.status,
            'total_cost': self.total_cost,
            'timestamp': self.timestamp,
            'items': [item.to_dict() for item in self.items]
        }
    

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default =1)
    price = db.Column(db.Float, nullable=False)
    order_time = db.Column(db.DateTime, default=datetime.now(ist))

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, dish_id={self.dish_id}, quantity={self.quantity}, price={self.price})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'dish_id': self.dish_id,
            'quantity': self.quantity,
            'price': self.price
        }


class Cart(db.Model):
    __tablename__ = 'cart'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_cart_user_id', ondelete='CASCADE'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('orders.session_id', name='fk_cart_session_id', ondelete='CASCADE'), nullable=False)
    items = db.relationship('CartItem', backref='cart', lazy=True, cascade="all, delete-orphan")
    total_cost = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f"Cart(id={self.id}, user_id={self.user_id}, session_id={self.session_id}, items_count={len(self.items)})"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "items": [item.to_dict() for item in self.items],
            "total_cost": self.total_cost
        }

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id',name='fk_cart_id', ondelete='CASCADE'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id', name = 'fk_cart_dish_name'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return (f"<CartItem(id={self.id}, cart_id={self.cart_id}, dish_id={self.dish_id}, "
                f"quantity={self.quantity}, price={self.price})>")

    def to_dict(self):
        return {
            "id": self.id,
            "dish_id": self.dish_id,
            "quantity": self.quantity,
            "price": self.price
        }

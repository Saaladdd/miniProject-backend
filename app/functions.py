from app.models import User, Preferences, Restaurant, Menu, Dish, Theme, Conversation
from app import db
import secrets
import base64
import hashlib
import os

def save_message(user_id, rest_id, role, content):
    try:
        db.session.add(Conversation(user_id=user_id, rest_id=rest_id, role=role, content=content))
        db.session.commit()
    except:
        db.session.rollback()

def get_conversation_history(user_id,rest_id):
    conversations = Conversation.query.filter_by(user_id=user_id,rest_id=rest_id).all()
    return [{"role": convo.role, "content": convo.content} for convo in conversations]

def get_restaurant_details(rest_id: int) -> str:
    rest = Restaurant.query.filter_by(id=rest_id).first()
    
    if not rest:
        return "Restaurant not found."

    rest_description = "This is the restaurant's details:"
    for key, value in rest.to_dict().items():
        rest_description += f"\n{key}: {value}"
        
    return rest_description

def get_filtered_menu_for_chatbot(menu_id, user_id):
    all_dishes = Dish.query.filter_by(menu_id=menu_id).all()
    filtered_dish_ids = sort_user_preferences(user_id, menu_id)
    filtered_dishes = [dish for dish in all_dishes if dish in filtered_dish_ids]
    filtered_menu_for_chatbot = "Here is the menu based on your preferences:\n\n"
    for dish in filtered_dishes:
        filtered_menu_for_chatbot += (
            f"ID: {dish.id}\n"
            f"Dish Name: {dish.dish_name}\n"
            f"Description: {dish.description or 'No description available'}\n"
            f"Price: ${dish.price:.2f}\n"
            f"Protein: {dish.protein}g, Fat: {dish.fat}g, Carbs: {dish.carbs}g, Energy: {dish.energy} kcal\n"
            f"Special Attributes: "
            f"{'Lactose-Free' if dish.is_lactose_free else 'Not Lacto-Free'} "
            f"{'Halal' if dish.is_halal else 'Not Halal'} "
            f"{'Vegan' if dish.is_vegan else 'Not Vegan'} "
            f"{'Vegetarian' if dish.is_vegetarian else 'Vegetarian'} "
            f"{'Gluten-Free' if dish.is_gluten_free else 'Not Gluten-Free'} "
            f"{'Jain' if dish.is_jain else 'Not Jain'} "
            f"{'Soy-Free' if dish.is_soy_free else 'Not Soy-Free'}\n"
            f"Available: {'Yes' if dish.is_available else 'No'}\n\n"
        )
    return filtered_menu_for_chatbot.strip()

def get_menu_for_chatbot(menu_id, user_id):
    menu = Menu.query.filter_by(id=menu_id).first()
    if not menu:
        return "Menu not found."
    all_dishes = Dish.query.filter_by(menu_id=menu_id).all()
    menu_for_chatbot = "Here is the unfiltered menu:\n\n"
    for dish in all_dishes:
        menu_for_chatbot += (
            f"ID: {dish.id}\n"
            f"Dish Name: {dish.dish_name}\n"
            f"Description: {dish.description or 'No description available'}\n"
            f"Price: ${dish.price:.2f}\n"
            f"Protein: {dish.protein}g, Fat: {dish.fat}g, Carbs: {dish.carbs}g, Energy: {dish.energy} kcal\n"
            f"Special Attributes: "
            f"{'Lactose-Free' if dish.is_lactose_free else 'Not Lacto-Free'} "
            f"{'Halal' if dish.is_halal else 'Not Halal'} "
            f"{'Vegan' if dish.is_vegan else 'Not Vegan'} "
            f"{'Vegetarian' if dish.is_vegetarian else 'Vegetarian'} "
            f"{'Gluten-Free' if dish.is_gluten_free else 'Not Gluten-Free'} "
            f"{'Jain' if dish.is_jain else 'Not Jain'} "
            f"{'Soy-Free' if dish.is_soy_free else 'Not Soy-Free'}\n"
            f"Available: {'Yes' if dish.is_available else 'No'}\n\n"
        )
    return menu_for_chatbot.strip()

def get_user_desc_string(user_id):
    preferences = Preferences.query.filter_by(user_id=user_id).all()
    user_string = "Here are the user's preferences:\n\n"

    if not preferences:
        return "No preferences found for this user."

    for pref in preferences:
        user_string += (
            f"Preference: {pref.preference}\n"
            f"Lactose Intolerant: {'Yes' if pref.is_lactose_intolerant else 'No'}\n"
            f"Halal: {'Yes' if pref.is_halal else 'No'}\n"
            f"Vegan: {'Yes' if pref.is_vegan else 'No'}\n"
            f"Vegetarian: {'Yes' if pref.is_vegetarian else 'No'}\n"
            f"Allergic to Gluten: {'Yes' if pref.is_allergic_to_gluten else 'No'}\n"
            f"Jain: {'Yes' if pref.is_jain else 'No'}\n\n"
        )
    return user_string.strip()

def sort_user_preferences(user_id,menu_id):
    user_preferences = Preferences.query.filter_by(user_id=user_id).first()
    menu = Menu.query.filter_by(id=menu_id).first()
    updated_menu =[]
    for dish in menu.dishes:
        dish = Dish.query.filter_by(id=dish.id).first()
        if user_preferences.is_lactose_intolerant and not dish.is_lactose_free:
            continue
        if  user_preferences.is_halal and not dish.is_halal:
            continue
        if  user_preferences.is_vegan and not dish.is_vegan:
            continue
        if  user_preferences.is_vegetarian and not dish.is_vegetarian:
            continue
        if  user_preferences.is_allergic_to_gluten and not dish.is_allergic_to_gluten:
            continue
        if  user_preferences.is_jain and not dish.is_jain:
            continue
        updated_menu.append(dish)
    return updated_menu

def generate_session_id(user_id):
    random_bytes = secrets.token_bytes(4)
    session_id = f"{user_id}-{base64.urlsafe_b64encode(random_bytes).decode()}"
    return session_id

def hash_filename(filename):
    name, extension = os.path.splitext(filename)
    hash_object = hashlib.md5(name.encode())
    unique_hash = hash_object.hexdigest()
    new_filename = f"{unique_hash}{extension}"
    return new_filename

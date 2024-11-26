from app.models import User, Preferences, Restaurant, Menu, Dish, Theme, Conversation,Cart
from app import db
import secrets
import base64
import hashlib
import os
import string
import random
from datetime import datetime
import re
import tiktoken
import json

def format_response(response):
    match = re.search(r'"text":\s*"([^"]*)"', response)
    if match:
        text_value = match.group(1)
    else:
        return None
    return text_value

def save_message(user_id, rest_id,session_id, role, content):
    try:
        if role == 'assistant':
            json_data = json.loads(content)['dishes']
            print(json_data)
            dish_ids = [item['dish_id'] for item in json_data]
            db.session.add(Conversation(user_id=user_id, rest_id=rest_id, role=role, content=format_response(content),session_id = session_id, dish_ids=dish_ids))
            db.session.commit()
        else:
            dish_ids = []
            db.session.add(Conversation(user_id=user_id, rest_id=rest_id, role=role, content=content,session_id = session_id, dish_ids=dish_ids))
            db.session.commit()
    except:
        db.session.rollback()

def get_conversation_history(user_id,rest_id,session_id):
    conversations = Conversation.query.filter_by(user_id=user_id,rest_id=rest_id,session_id=session_id).all()
    return [{"role": convo.role, "content": convo.content} for convo in conversations]

def get_restaurant_details(rest_id: int) -> str:
    rest = Restaurant.query.filter_by(id=rest_id).first()
    
    if not rest:
        return "Restaurant not found."

    rest_description = "This is the restaurant's details:"
    for key, value in rest.to_dict().items():
        rest_description += f"\n{key}: {value}"
        
    return rest_description

def get_filtered_menu_for_chatbot(rest_id, user_id):
    menus = Menu.query.filter_by(restaurant_id=rest_id).all()
    menu_details = "Here is the menu based on your preferences:\n\n"
    for menu in menus:
        menu_details += (
            f"Menu ID: {menu.id}\n"
            f"Menu Name: {menu.menu_type or 'No name provided'}\n\n"
        )
        all_dishes = Dish.query.filter_by(menu_id=menu.id).all()
        filtered_dish_ids = sort_user_preferences(user_id, menu.id)
        filtered_dishes = [dish for dish in all_dishes if dish.id in filtered_dish_ids]
        if not filtered_dishes:
            menu_details += "No dishes available for this menu based on your preferences.\n\n"
            continue
        
        for dish in filtered_dishes:
            menu_details += (
                f"  Dish ID: {dish.id}\n"
                f"  Dish Name: {dish.dish_name}\n"
                f"  Description: {dish.description or 'No description available'}\n"
                f"  Price: ${dish.price:.2f}\n"
                f"  Protein: {dish.protein}g, Fat: {dish.fat}g, Carbs: {dish.carbs}g, Energy: {dish.energy} kcal\n"
                f"  Special Attributes: "
                f"{'Lactose-Free' if dish.is_lactose_free else 'Not Lacto-Free'}, "
                f"{'Halal' if dish.is_halal else 'Not Halal'}, "
                f"{'Vegan' if dish.is_vegan else 'Not Vegan'}, "
                f"{'Vegetarian' if dish.is_vegetarian else 'Vegetarian'}, "
                f"{'Gluten-Free' if dish.is_gluten_free else 'Not Gluten-Free'}, "
                f"{'Jain' if dish.is_jain else 'Not Jain'}, "
                f"{'Soy-Free' if dish.is_soy_free else 'Not Soy-Free'}\n"
                f"  Available: {'Yes' if dish.is_available else 'No'}\n\n"
            )
    return menu_details.strip()

def get_menu_for_chatbot(rest_id):
    menus = Menu.query.filter_by(restaurant_id=rest_id).all()
    
    if not menus:
        return "No menus found for this restaurant."
  
    menu_details = "Here are all the menus and their dishes for this restaurant:\n\n"
    
    for menu in menus:
       
        menu_details += (
            f"Menu ID: {menu.id}\n"
            f"Menu Name: {menu.menu_type or 'Unnamed Menu'}\n\n"
        )
        all_dishes = Dish.query.filter_by(menu_id=menu.id).all()
        
        if not all_dishes:
            menu_details += "  No dishes available for this menu.\n\n"
            continue
        
        for dish in all_dishes:
            menu_details += (
                f"  Dish ID: {dish.id}\n"
                f"  Dish Name: {dish.dish_name}\n"
                f"  Description: {dish.description or 'No description available'}\n"
                f"  Price: ${dish.price:.2f}\n"
                f"  Protein: {dish.protein}g, Fat: {dish.fat}g, Carbs: {dish.carbs}g, Energy: {dish.energy} kcal\n"
                f"  Special Attributes: "
                f"{'Lactose-Free' if dish.is_lactose_free else 'Not Lacto-Free'}, "
                f"{'Halal' if dish.is_halal else 'Not Halal'}, "
                f"{'Vegan' if dish.is_vegan else 'Not Vegan'}, "
                f"{'Vegetarian' if dish.is_vegetarian else 'Vegetarian'}, "
                f"{'Gluten-Free' if dish.is_gluten_free else 'Not Gluten-Free'}, "
                f"{'Jain' if dish.is_jain else 'Not Jain'}, "
                f"{'Soy-Free' if dish.is_soy_free else 'Not Soy-Free'}\n"
                f"  Available: {'Yes' if dish.is_available else 'No'}\n\n"
            )
    
    return menu_details.strip()

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
    raw_id = f"{user_id}{int(datetime.utcnow().timestamp())}"
    session_id = int(hashlib.md5(raw_id.encode()).hexdigest(), 16) % (10**7)
    return session_id

def hash_filename(filename):
    print(filename)
    name, extension = os.path.splitext(filename)
    hash_object = hashlib.md5(name.encode())
    unique_hash = hash_object.hexdigest()
    new_filename = f"{unique_hash}{extension}"
    return new_filename

def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choices(characters, k=length))
    return random_string

def return_link(filename):
    return f"http://localhost:5000/uploads/{filename}"



def count_tokens(messages, model="gpt-4o"):
    """Count the number of tokens in the message list using the OpenAI tokenizer."""
    # Initialize tokenizer
    tokenizer = tiktoken.get_encoding("gpt2" if model == "gpt-4o" else "cl100k_base")
    
    # Count tokens for each message
    total_tokens = 0
    for message in messages:
        total_tokens += len(tokenizer.encode(message["content"]))
    
    return total_tokens

def clear_cart(row_id):
    # Get the row by its ID
    row = Cart.query.get(row_id)
    if row:
        # Set all columns to None, except the ID (or primary key)
        for column in Cart.__table__.columns.keys():
            if column != "id":  # Keep the ID column intact
                setattr(row, column, None)
        db.session.commit()
        return "Row cleared successfully."
    return "Row not found."
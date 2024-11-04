from openai import OpenAI
from flask import request,jsonify
from app.models import Preferences,Menu,Conversation,Dish
from app import db
from app.functions import sort_user_preferences

def save_message(user_id,role, content):
    new_message = Conversation(user_id=user_id,role=role, content=content)
    db.session.add(new_message) 
    db.session.commit()

def get_conversation_history(user_id):
    conversations = Conversation.query.filter_by(user_id=user_id).all()
    return [{"role": convo.role, "content": convo.content} for convo in conversations]
    
def get_menu_for_chatbot(menu_id, user_id):
    filtered_dish_ids = sort_user_preferences(user_id, menu_id)
    dishes = Dish.query.filter(Dish.id.in_(filtered_dish_ids)).all()
    menu_for_chatbot = "Here is the menu based on your preferences:\n\n"
    for dish in dishes:
        menu_for_chatbot += (
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
    preferences = Preferences.query.filter_by(user_id=user_id).all()  # Fetch all preferences associated with user
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
    
def chatbot_chat(user_id, user_input,api_key):
    client = OpenAI(
        api_key= api_key
    )
    user_description = Conversation.query.get(user_id=user_id).user_description 
    history= get_conversation_history(user_id)

    messages=  [{
                "role": "system", "content": """You are a restaurant assistant/chatbot. You will be chat with the user.
                                                You will also take into consideration the user preferences and the older
                                                chat history which will be fed to you. You will also be fed the restaurant
                                                details and the menu details. Make sure to be careful with the user allergies
                                                and the dish information. DO NOT at any cost reccomend dishes which do not align
                                                with the user preferences. Don't deviate from the topic and answer based on the
                                                information presented to you and be faithful to being a restaurant assisant of the
                                                restaurant assigned to you. Make sure to sound friendly and use the customers name
                                                if required.
                                             """     
                },
                {"role": "system", "content": f"The user description is:{user_description}"}
                
                ]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})
    try:
        chat_completion = client.chat.completions.create(
            messages= messages,
            model ="gpt-4o",
            temperature= 0.3,
            max_tokens= 1000
        )
        response = chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return jsonify({"error": "An error occurred while processing your request.", "details": str(e)}), 500
        
    save_message(user_id, "user",user_input)
    save_message(user_id,"assistant",response)
    return jsonify({"reply":response}),200

def create_user_description(user_id, api_key):
    client = OpenAI(
        api_key= api_key
    )
    input = get_user_desc_string(user_id)
    messages=  [{
                "role": "system", "content": """You will create a user description based on his preferences. This
                                                description should be in less than 50 words. This description will be
                                                used for decieding on allergies and food preferences. So be extremely
                                                careful.
                                             """     
                },
                {"role": "user", "content": input}
                ]
    try:
        response = client.chat.completions.create(
            messages= messages,
            model ="gpt-4o",
            temperature= 0.3,
            max_tokens= 100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    
    

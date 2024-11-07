from openai import OpenAI
from flask import request,jsonify
from myapp.models import Preferences,Menu,Conversation,Dish,User,Restaurant
from myapp import db
from myapp.functions import sort_user_preferences, generate_session_id, get_user_desc_string, get_conversation_history, save_message, get_menu_for_chatbot, get_filtered_menu_for_chatbot   

    
def chatbot_chat(user_id: int, rest_id: int, menu_id: int, user_input: str, api_key):
    
    client = OpenAI(api_key=api_key)

    user = User.query.filter_by(id=user_id).first()
    user_description = user.user_description

    history = get_conversation_history(user_id, rest_id)

    filtered_menu = get_filtered_menu_for_chatbot(menu_id, user_id)
    unfiltered_menu = get_menu_for_chatbot(menu_id, user_id)

    messages = [
        {
            "role": "system",
            "content": """
            You are a restaurant assistant/chatbot. You will be chat with the user.
            You will also take into consideration the user preferences and the older
            chat history which will be fed to you. You will also be fed the restaurant
            details and the menu details. You as a chatbot will be used for multiple Restaurants
            so only give feedback based on the restaurant the user is currently dining at. Donot
            give any personal information.. Make sure to be careful with the user allergies
            and the dish information. DO NOT at any cost reccomend dishes which do not align
            with the user preferences. Don't deviate from the topic and answer based on the
            information presented to you and be faithful to being a restaurant assisant of the
            restaurant assigned to you. Make sure to sound friendly and use the customers name
            if required.
            """
        },
        {"role": "system", "content": f"The user description is:{user_description}"},
        {"role": "system", "content": f"The filtered menu is: {filtered_menu}"},
        {"role": "system", "content": f"The unfiltered menu is: {unfiltered_menu}"}
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})
    try:
        chat_completion = client.chat.completions.create(
            messages= messages,
            model ="gpt-3.5-turbo",
            temperature= 0.3,
            max_tokens= 1000
        )
        response = chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return jsonify({"error": "An error occurred while processing your request.", "details": str(e)}), 500
        
    save_message(user_id,rest_id, "user",user_input)
    save_message(user_id,rest_id,"assistant",response)
    return jsonify({"reply":response}),200

def create_user_description(user_id: int, api_key: str) -> str:
    client = OpenAI(api_key=api_key)
    input_str = get_user_desc_string(user_id)
    messages = [
        {
            "role": "system",
            "content": """You will create a user description based on his preferences. This
                            description should be in less than 50 words. This description will be
                            used for decieding on allergies and food preferences. So be extremely
                            careful. Also make sure to use proper punctuations.
                         """
        },
        {"role": "user", "content": input_str}
    ]
    try:
        response = client.chat.completions.create(
            messages=messages,
            model="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    
    

from openai import OpenAI
from flask import jsonify
from app.models import Preferences,Menu,Conversation,Dish,User,Restaurant
from app import db
from app.functions import get_user_desc_string, get_conversation_history, save_message, get_menu_for_chatbot, get_filtered_menu_for_chatbot, get_restaurant_details,count_tokens

    
def chatbot_chat(user_id: int, rest_id: int, user_input: str, session_id: int, api_key):
    
    client = OpenAI(api_key=api_key)

    user = User.query.filter_by(id=user_id).first()
    user_description = user.user_description

    history = get_conversation_history(user_id, rest_id,session_id)

    filtered_menu = get_filtered_menu_for_chatbot(rest_id, user_id)
    unfiltered_menu = get_menu_for_chatbot(rest_id)
    restaurant_details = get_restaurant_details(rest_id)

    messages = [
    {
        "role": "system",
        "content": """
            You are a restaurant assistant chatbot. Use past chat history, user preferences, and menu details to recommend dishes based on the user's context. Be attentive to allergies and preferences. Stay on topic and be friendly.
            Instructions for Output:
            1.When recommending dishes, return only "dishes" with dish_id values (do not include dish id in text).
            2.If the user asks for a cuisine outside the restaurant's main cuisine, suggest available items.
            3.If menu is requested, return a list of dish_ids under "dishes".
            4.If you name the dish, REMEMBER to always return dish_ids too unless its unavailable.
            5.If no dishes are needed, return only the "text" key  
            6.Don't use markup tags.
            7.At any cost do not go out of context of being a restaurant chatbot!
        """
    },
    {"role": "system", "content": f"The user description is: {user_description}"},
    {"role": "system", "content": f"The restaurant details are: {restaurant_details}"},
    {"role": "system", "content": f"The filtered menu is: {filtered_menu}"},
    {"role": "system", "content": f"The unfiltered menu is: {unfiltered_menu}"},
    {
        "role": "system",
        "content": """
            If no dishes are needed, return empty list. Always return in JSON format with "text" and "dishes" keys.
            Example: {\"text\": \"Sure, here are the sweet dishes:\", \"dishes\": [{\"dish_id\": 1}, {\"dish_id\": 2}, {\"dish_id\": 3}]
            Im using the output to feed to a function so the response must be constantly in the example format.
        """
    }
]
    messages= history + messages
    messages.append({"role": "user", "content": user_input})
    print(count_tokens(messages))

    try:
        chat_completion = client.chat.completions.create(
            messages= messages,
            model ="gpt-4o",
            temperature= 0,
            max_tokens= 2500
        )
        response = chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return jsonify({"error": "An error occurred while processing your request.", "details": str(e)}), 500
        
    save_message(user_id,rest_id,session_id,"user",user_input)
    print(response)
    save_message(user_id,rest_id,session_id,"assistant",response)
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
    
    

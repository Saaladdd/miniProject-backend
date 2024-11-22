from openai import OpenAI
from flask import request,jsonify
from app.models import Preferences,Menu,Conversation,Dish,User,Restaurant
from app import db
from app.functions import get_user_desc_string, get_conversation_history, save_message, get_menu_for_chatbot, get_filtered_menu_for_chatbot, get_restaurant_details,format_response,count_tokens

    
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
                    You are a restaurant assistant chatbot that interacts with users. Use past chat history, user preferences, and provided restaurant and menu details to offer recommendations specific to the restaurant the user is currently dining at. Be attentive to allergies and user preferences, and never suggest items that don’t align with these. Stay on topic, be friendly.
                    Instructions for Output:
                    When recommending dishes, use the key "dishes" with a list of dish_id values only.
                    When no dish details are required, use only the "text" key.
                    If a user requests a cuisine different from the restaurant’s main cuisine (e.g., Italian items at a Chinese restaurant), carefully search the menu and suggest relevant items if available.
                    Whenever you include the dish name, always include the dish_id with the response text in JSON.
                    If menu is requested send the dish_id's as a list with key as dishes with a text reponse.
                    If the user asks to order any dish ALWAYS return the dish ids too. Dont include id in the text response.
                """
            },
            {"role": "system", "content": f"The user description is:{user_description}"},
            {"role": "system", "content": f"The restaurant details are:{restaurant_details}"},
            {"role": "system", "content": f"The filtered menu is: {filtered_menu}"},
            {"role": "system", "content": f"The unfiltered menu is: {unfiltered_menu}"},
            {
            "role": "system",
            "content": """If dishes are not required return None.
                        Every response must be of this format donot use ANY other formats:
                        {\"text\": \"Sure, here are the sweet dishes:\", \"dishes\": [{\"dish_id\": 1}, {\"dish_id\": 2}, {\"dish_id\": 3}]}
                        Also if the user enquires anything else except dishes BUT within the restaurant context then return the json with the text.
                        Always return in json and keys as text and dishes no matter what.
                        """
            }                               
                                            
    ]
    messages.extend(history)
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
        
    save_message(user_id,rest_id,session_id, "user",user_input)
    print(response)
    assistant_response = format_response(response)
    save_message(user_id,rest_id,session_id,"assistant",assistant_response)
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
    
    

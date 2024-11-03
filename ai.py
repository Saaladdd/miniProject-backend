from openai import OpenAI
from flask import request,jsonify
from app.models import Preferences,Menu,Conversation
from app import db


def save_message(user_id,role, content):
    new_message = Conversation(user_id=user_id,role=role, content=content)
    db.session.add(new_message) 
    db.session.commit()

def get_conversation_history(user_id):
    conversations = Conversation.query.filter_by(user_id=user_id).all()
    return [{"role": convo.role, "content": convo.content} for convo in conversations]
    
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

def create_user_description(user_id):
    preferences = Preferences.query.filter_by(user_id=user_id).first()
    

# # original
# import openai
# import os
# from openai import OpenAI
# from flask import Flask, render_template, request, jsonify, session
# from flask_cors import CORS
# from flask_session import Session


# os.environ["OPENAI_API_KEY"] = os.getenv('API_KEY')

# app = Flask(__name__)
# CORS(app)
# app.config["SECRET_KEY"] = "KOREABC"
# app.config["SESSION_TYPE"] = "filesystem"
# Session(app)
# client = OpenAI()

# @app.route('/ask', methods=['POST'])
# def ask():
#     try:
#         if "chat_history" not in session:
#             session["chat_history"] = []  # Initialize chat history in session
        
#         data = request.get_json()
#         input_text = data.get("query", "")

#         if not input_text:
#             return jsonify({"error": "No input provided"}), 400

#         # Define the system prompt and user-specific prompt
#         prompt = f"Answer the user's query only in Telugu with correct grammar: {input_text}. Do not translate that query; just analyze and respond appropriately. Remember all conversations so that even if user asks about a conversation from somewhere in between past conversations you should be able to answer that."

#         # Append the current user input to chat history
#         session["chat_history"].append({"role": "user", "content": input_text})

#         # Build the message list for the API, including chat history
#         messages = [{"role": "system", "content": "You are a helpful assistant."}] + session["chat_history"]

#         # Add the current prompt to the messages
#         messages.append({"role": "user", "content": prompt})

#         # Call the ChatGPT API
#         completion = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=messages
#         )

#         # Extract the response content
#         response_text = completion.choices[0].message.content.strip()

#         # Append the assistant's response to chat history
#         session["chat_history"].append({"role": "assistant", "content": response_text})
#         session.modified = True  # Mark session as modified to save changes

#         # Return the response as JSON
#         return jsonify({"response": response_text})
#     except Exception as e:
#         # Handle exceptions gracefully
#         return jsonify({"error": str(e)}), 500

# # def generate_Telugu_Response(input_text):
# #     print("IN GENERATE RESPONSE . . . . .")
    
# # print(generate_Telugu_Response(text))

# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 5000)) 
#     app.run(host='0.0.0.0', port=port, debug=True)
import openai
import os
from openai import OpenAI
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_session import Session
from datetime import timedelta

os.environ["OPENAI_API_KEY"] = os.getenv('API_KEY')

app = Flask(__name__)

# Updated CORS configuration
CORS(app, 
     resources={r"/ask": {"origins": ["http://localhost:5000", "https://your-frontend-domain.com"],
                         "methods": ["POST", "OPTIONS"],
                         "allow_headers": ["Content-Type"],
                         "supports_credentials": True}},
     supports_credentials=True)

# Session configuration
app.config.update(
    SECRET_KEY="KOREABC",
    SESSION_TYPE="filesystem",
    SESSION_PERMANENT=True,
    PERMANENT_SESSION_LIFETIME=timedelta(days=1),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='None'
)

Session(app)
client = OpenAI()

@app.after_request
def after_request(response):
    """Add headers to every response."""
    origin = request.headers.get('Origin', '')
    if origin in ["http://localhost:5000", "https://your-frontend-domain.com"]:
        response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# ... rest of your existing code ...
def extract_key_information(text, response):
    """Helper function to identify and store key information from conversations"""
    messages = [
        {"role": "system", "content": """Extract key information from this conversation if present.
        Look for details about: names, properties, belongings, relationships, etc.
        Format output as a dictionary with nested structure when needed.
        Example: {"car": {"name": "Safari", "color": "red"}}
        If no key info, return empty dict."""},
        {"role": "user", "content": f"User said: {text}\nAssistant replied: {response}"}
    ]
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        info = eval(completion.choices[0].message.content)
        return info if isinstance(info, dict) else {}
    except:
        return {}

def merge_memory(existing_memory, new_info):
    """Merge new information with existing memory, preserving nested structures"""
    merged = existing_memory.copy()
    for key, value in new_info.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged

@app.route('/ask', methods=['POST'])
def ask():
    try:
        # Ensure session is working
        if not session.get("initialized"):
            session["initialized"] = True
            session["memory"] = {}
            session["chat_history"] = []
            session.modified = True
        
        # Debug print
        print("Current session memory before processing:", session.get("memory", {}))
        
        data = request.get_json()
        input_text = data.get("query", "")

        if not input_text:
            return jsonify({"error": "No input provided"}), 400

        # Create memory context
        memory = session.get("memory", {})
        memory_context = ""
        if memory:
            context_parts = []
            for entity, details in memory.items():
                if isinstance(details, dict):
                    properties = [f"{k} is {v}" for k, v in details.items()]
                    context_parts.append(f"The {entity} {' and '.join(properties)}")
            memory_context = "Known information: " + " ".join(context_parts)

        # System prompt with memory context
        system_prompt = f"""You are a helpful assistant that responds only in Telugu with correct grammar.
        IMPORTANT - Current Memory: {memory_context}
        You MUST use this stored information to answer questions about previously mentioned details.
        Answer the query appropriately without translating the question itself."""

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text}
        ]

        # Call the ChatGPT API
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        # Extract the response
        response_text = completion.choices[0].message.content.strip()

        # Extract and merge new information
        new_info = extract_key_information(input_text, response_text)
        if new_info:
            updated_memory = merge_memory(session.get("memory", {}), new_info)
            session["memory"] = updated_memory
            
        # Update chat history
        chat_history = session.get("chat_history", [])
        chat_history.append({"role": "user", "content": input_text})
        chat_history.append({"role": "assistant", "content": response_text})
        
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]
            
        session["chat_history"] = chat_history
        session.modified = True  # Mark session as modified
        
        # Debug print
        print("Updated session memory:", session.get("memory", {}))

        return jsonify({
            "response": response_text,
            "memory": session.get("memory", {})
        })

    except Exception as e:
        print(f"Error in ask route: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Create session directory if it doesn't exist
os.makedirs("./flask_session", exist_ok=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
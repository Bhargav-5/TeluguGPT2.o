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

os.environ["OPENAI_API_KEY"] = os.getenv('API_KEY')

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = "KOREABC"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
client = OpenAI()

def extract_key_information(text, response):
    """Helper function to identify and store key information from conversations"""
    # Add system message to help identify key information
    messages = [
        {"role": "system", "content": "Extract key information from this conversation if present. "
                                    "Look for details about: names, properties, belongings, relationships, etc. "
                                    "Format: JSON-like key-value pairs. If no key info, return empty dict."},
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

@app.route('/ask', methods=['POST'])
def ask():
    try:
        # Initialize session variables if they don't exist
        if "chat_history" not in session:
            session["chat_history"] = []
        if "memory" not in session:
            session["memory"] = {}
        
        data = request.get_json()
        input_text = data.get("query", "")

        if not input_text:
            return jsonify({"error": "No input provided"}), 400

        # Build context from memory
        memory_context = "Known information: " + ". ".join([f"{k}: {v}" for k, v in session["memory"].items()]) if session["memory"] else ""
        
        # Define the system prompt with memory context
        system_prompt = """You are a helpful assistant that responds only in Telugu with correct grammar. 
        Remember and use this information in your responses: {memory_context}
        Answer the query appropriately without translating the question itself."""

        # Build messages list with chat history and memory
        messages = [
            {"role": "system", "content": system_prompt.format(memory_context=memory_context)}
        ] + session["chat_history"]

        # Add the current query
        messages.append({"role": "user", "content": input_text})

        # Call the ChatGPT API
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        # Extract the response
        response_text = completion.choices[0].message.content.strip()

        # Extract and store key information from the conversation
        new_info = extract_key_information(input_text, response_text)
        if new_info:
            session["memory"].update(new_info)

        # Update chat history
        session["chat_history"].append({"role": "user", "content": input_text})
        session["chat_history"].append({"role": "assistant", "content": response_text})
        
        # Limit chat history length to prevent token limits
        if len(session["chat_history"]) > 20:  # Keep last 10 exchanges
            session["chat_history"] = session["chat_history"][-20:]
        
        session.modified = True

        return jsonify({
            "response": response_text,
            "memory": session["memory"]  # Optional: return current memory state for debugging
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
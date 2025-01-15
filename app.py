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
#         prompt = f"Answer the user's query only in Telugu with correct grammar: {input_text}. Do not translate that query; just analyze and respond appropriately. Remember all chats."

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
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_session import Session
from datetime import datetime

os.environ["OPENAI_API_KEY"] = os.getenv('API_KEY')

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = "KOREABC"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

client = openai

MAX_HISTORY_LENGTH = 10  # Limit the number of conversation history to store

@app.route('/ask', methods=['POST'])
def ask():
    try:
        # Get the query from the request
        data = request.get_json()
        query = data.get("query", "")
        
        if not query:
            return jsonify({"error": "No input provided"}), 400
        
        # Initialize chat history if not exists
        if "conversations" not in session:
            session["conversations"] = []

        # Add user query to conversation history
        session["conversations"].append({
            "role": "user",
            "content": query,
            "timestamp": datetime.now().isoformat()
        })
        
        # Create conversation context for the model
        context = "\n".join([
            f"{conv['role'].capitalize()}: {conv['content']}"
            for conv in session["conversations"][-MAX_HISTORY_LENGTH:]
        ])

        # Prepare the system prompt
        prompt = f"Based on our conversation, answer the following query in Telugu. {context}\nUser's query: {query}"

        # Call OpenAI API with the conversation context
        response = client.ChatCompletion.create(
            model="gpt-4o-mini",  # Ensure you're using the correct model
            messages=[{"role": "system", "content": "You are a helpful assistant who responds in Telugu."}] + [{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7,
        )
        
        response_text = response['choices'][0]['message']['content'].strip()

        # Append assistant response to conversation history
        session["conversations"].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now().isoformat()
        })
        session.modified = True  # Mark session as modified to store the conversation history
        
        return jsonify({"response": response_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset_conversation():
    try:
        session["conversations"] = []  # Reset conversation history
        session.modified = True
        return jsonify({"message": "Conversation reset successful"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

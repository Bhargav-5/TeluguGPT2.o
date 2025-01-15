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

@app.route('/ask', methods=['POST'])
def ask():
    try:
        if "chat_history" not in session:
            session["chat_history"] = []  # Initialize chat history in session
        
        data = request.get_json()
        input_text = data.get("query", "")

        if not input_text:
            return jsonify({"error": "No input provided"}), 400

        # Define the system prompt and user-specific prompt
        prompt = f"Answer the user's query only in Telugu with correct grammar: {input_text}. Do not translate that query; just analyze and respond appropriately. Remember all chats."

        # Append the current user input to chat history
        session["chat_history"].append({"role": "user", "content": input_text})

        # Build the message list for the API, including chat history
        messages = [{"role": "system", "content": "You are a helpful assistant."}] + session["chat_history"]

        # Add the current prompt to the messages
        messages.append({"role": "user", "content": prompt})

        # Call the ChatGPT API
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        # Extract the response content
        response_text = completion.choices[0].message.content.strip()

        # Append the assistant's response to chat history
        session["chat_history"].append({"role": "assistant", "content": response_text})
        session.modified = True  # Mark session as modified to save changes

        # Return the response as JSON
        return jsonify({"response": response_text})
    except Exception as e:
        # Handle exceptions gracefully
        return jsonify({"error": str(e)}), 500

# def generate_Telugu_Response(input_text):
#     print("IN GENERATE RESPONSE . . . . .")
    
# print(generate_Telugu_Response(text))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) 
    app.run(host='0.0.0.0', port=port, debug=True)

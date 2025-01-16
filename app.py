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
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_session import Session
from datetime import timedelta

# Load the API key
openai.api_key = os.getenv('API_KEY')

app = Flask(__name__)

# CORS configuration
CORS(app, 
     resources={r"/ask": {"origins": ["http://localhost:5500", "https://your-frontend-domain.com"]}},
     supports_credentials=True)

# Session configuration
app.config.update(
    SECRET_KEY="KOREABC",
    SESSION_TYPE="filesystem",
    PERMANENT_SESSION_LIFETIME=timedelta(days=1),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="None"
)

Session(app)

@app.route('/ask', methods=['POST'])
def ask():
    try:
        if "memory" not in session:
            session["memory"] = {}
        
        user_query = request.json.get("query", "")
        memory_context = " ".join(
            [f"{k}: {v}" for k, v in session['memory'].items()]
        )

        system_prompt = f"""
You are a helpful assistant who responds only in Telugu. Here is some context from previous interactions:
{memory_context}
Respond to the following query appropriately:
"""

        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]
        )

        # Get the generated response
        assistant_reply = response['choices'][0]['message']['content'].strip()

        # Simulate extracting key-value pairs for memory update
        new_memory = {"key": "value"}  # Example new memory (replace with actual extraction logic)
        session["memory"].update(new_memory)

        return jsonify({
            "response": assistant_reply,
            "memory": session["memory"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

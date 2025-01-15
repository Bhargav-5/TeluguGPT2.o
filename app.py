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
from openai import OpenAI
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_session import Session
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = os.getenv('API_KEY')

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = "KOREABC"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
client = OpenAI()

MAX_HISTORY_LENGTH = 10
SYSTEM_PROMPT = """You are a helpful assistant who responds in Telugu. 
Maintain context of the conversation and refer to previous topics when relevant.
Use consistent Telugu terminology throughout the conversation.
If the user refers to something mentioned earlier, acknowledge it in your response."""

@app.route('/ask', methods=['POST'])
def ask():
    try:
        # Log incoming request
        logger.debug("Received request: %s", request.get_json())
        
        if "chat_history" not in session:
            session["chat_history"] = []
            session["conversation_start"] = datetime.now().isoformat()
            logger.debug("Initialized new chat history")
        
        data = request.get_json()
        input_text = data.get("query", "")
        
        logger.debug("Input text: %s", input_text)

        if not input_text:
            logger.error("No input provided")
            return jsonify({"error": "No input provided"}), 400

        # Log current session state
        logger.debug("Current chat history length: %d", len(session.get("chat_history", [])))
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(session["chat_history"][-MAX_HISTORY_LENGTH*2:])
        
        current_prompt = (f"Answer the following query in Telugu, maintaining context "
                         f"from our previous conversation, remember our conversations so that in future if user asks about past conversation you should be able to answer to it: {input_text}")
        messages.append({"role": "user", "content": current_prompt})
        
        logger.debug("Sending messages to OpenAI: %s", messages)

        # Verify API key is set
        api_key = os.getenv('API_KEY')
        if not api_key:
            logger.error("API key is not set")
            return jsonify({"error": "OpenAI API key is not configured"}), 500

        try:
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Changed from gpt-4o-mini to a valid model name
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            logger.debug("Received response from OpenAI")
            response_text = completion.choices[0].message.content.strip()
            logger.debug("Response text: %s", response_text)

        except openai.APIError as e:
            logger.error("OpenAI API error: %s", str(e))
            return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

        # Update chat history
        session["chat_history"].append({"role": "user", "content": input_text})
        session["chat_history"].append({"role": "assistant", "content": response_text})
        
        if len(session["chat_history"]) > MAX_HISTORY_LENGTH * 2:
            session["chat_history"] = session["chat_history"][-MAX_HISTORY_LENGTH*2:]
        
        session.modified = True
        
        logger.debug("Sending response back to client")
        return jsonify({
            "response": response_text,
            "conversation_length": len(session["chat_history"]) // 2,
            "conversation_start": session["conversation_start"]
        })

    except Exception as e:
        logger.error("Error in /ask endpoint: %s", str(e), exc_info=True)
        return jsonify({
            "error": str(e),
            "message": "An error occurred while processing your request"
        }), 500

@app.route('/reset', methods=['POST'])
def reset_conversation():
    try:
        session["chat_history"] = []
        session["conversation_start"] = datetime.now().isoformat()
        session.modified = True
        logger.debug("Chat history reset successfully")
        return jsonify({"message": "Conversation history reset successfully"})
    except Exception as e:
        logger.error("Error in /reset endpoint: %s", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
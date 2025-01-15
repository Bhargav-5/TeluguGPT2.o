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
import json

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

MAX_HISTORY_LENGTH = 20  # Increased history length for better memory
SYSTEM_PROMPT = """You are a helpful assistant who responds in Telugu. Important instructions:
1. Always maintain full context of ALL previous conversations
2. When user refers to past conversations, search through the chat history provided
3. Keep track of important details mentioned in previous messages
4. Use consistent terminology throughout the conversation
5. Before responding, review the entire conversation history provided
6. If user asks about something discussed before, reference the specific previous conversation

Your mission is to maintain perfect conversational memory and context."""

@app.route('/ask', methods=['POST'])
def ask():
    try:
        # Log incoming request
        logger.debug("Received request: %s", request.get_json())
        
        # Initialize or load chat history
        if "chat_history" not in session:
            session["chat_history"] = []
            session["conversation_start"] = datetime.now().isoformat()
            session["context_summary"] = ""
            logger.debug("Initialized new chat history")
        
        data = request.get_json()
        input_text = data.get("query", "")
        
        logger.debug("Input text: %s", input_text)

        if not input_text:
            logger.error("No input provided")
            return jsonify({"error": "No input provided"}), 400

        # Build context-aware messages
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add context summary if exists
        if session.get("context_summary"):
            messages.append({
                "role": "system", 
                "content": f"Previous conversation summary: {session['context_summary']}"
            })
        
        # Add chat history
        messages.extend(session["chat_history"][-MAX_HISTORY_LENGTH*2:])
        
        # Create a context-aware prompt
        current_prompt = (
            f"Previous conversation context: {json.dumps(session['chat_history'][-10:], ensure_ascii=False)}\n\n"
            f"User's current query: {input_text}\n\n"
            "Remember all details from our previous conversations and answer in Telugu. "
            "If this query relates to any previous conversations, explicitly reference them in your response."
        )
        
        messages.append({"role": "user", "content": current_prompt})
        
        logger.debug("Sending messages to OpenAI: %s", messages)

        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",  # Using GPT-4 for better memory and context handling
                messages=messages,
                temperature=0.7,
                max_tokens=1000  # Increased for more detailed responses
            )
            
            logger.debug("Received response from OpenAI")
            response_text = completion.choices[0].message.content.strip()
            logger.debug("Response text: %s", response_text)

        except openai.APIError as e:
            logger.error("OpenAI API error: %s", str(e))
            return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

        # Update chat history with both query and response
        session["chat_history"].append({"role": "user", "content": input_text})
        session["chat_history"].append({"role": "assistant", "content": response_text})
        
        # Update context summary periodically
        if len(session["chat_history"]) % 10 == 0:
            summary_messages = [
                {"role": "system", "content": "Summarize the key points from this conversation history:"},
                {"role": "user", "content": str(session["chat_history"][-10:])}
            ]
            try:
                summary = client.chat.completions.create(
                    model="gpt-4",
                    messages=summary_messages,
                    temperature=0.3,
                    max_tokens=200
                )
                session["context_summary"] = summary.choices[0].message.content
            except Exception as e:
                logger.error("Error creating summary: %s", str(e))
        
        # Maintain history length
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
        session["context_summary"] = ""
        session.modified = True
        logger.debug("Chat history reset successfully")
        return jsonify({"message": "Conversation history reset successfully"})
    except Exception as e:
        logger.error("Error in /reset endpoint: %s", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
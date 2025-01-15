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

@app.route('/chat-history', methods=['GET'])
def get_chat_history():
    try:
        # Return all conversations from session
        conversations = session.get("conversations", [])
        return jsonify({
            "history": conversations,
            "total_messages": len(conversations)
        })
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    try:
        # Get the query from payload
        data = request.get_json()
        query = data.get("query", "")
        logger.debug(f"Received query: {query}")

        # Initialize chat history if not exists
        if "conversations" not in session:
            session["conversations"] = []

        # Add the current query to conversations
        session["conversations"].append({
            "query": query,
            "timestamp": datetime.now().isoformat()
        })

        # Build conversation context from previous queries
        context = "\n".join([
            f"Previous query: {conv['query']}\nResponse: {conv.get('response', '')}"
            for conv in session["conversations"][-MAX_HISTORY_LENGTH:]
        ])

        # Prepare messages for the API
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant who responds in Telugu. Remember our previous conversation context."
            },
            {
                "role": "user",
                "content": f"""Context of our conversation:
                {context}

                Current query: {query}

                Please respond in Telugu, considering all previous context."""
            }
        ]

        # Call API
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            response_text = completion.choices[0].message.content.strip()
            logger.debug(f"Response: {response_text}")

            # Store the response in conversations
            session["conversations"][-1]["response"] = response_text
            
            # Maintain history length
            if len(session["conversations"]) > MAX_HISTORY_LENGTH:
                session["conversations"] = session["conversations"][-MAX_HISTORY_LENGTH:]
            
            session.modified = True

            return jsonify({
                "response": response_text,
                "history": session["conversations"]  # Include history in response
            })

        except Exception as e:
            logger.error(f"API error: {str(e)}")
            return jsonify({"error": f"API error: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"Error in /ask endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset_conversation():
    try:
        session["conversations"] = []
        session.modified = True
        return jsonify({"message": "Conversation reset successful"})
    except Exception as e:
        logger.error(f"Error in reset: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
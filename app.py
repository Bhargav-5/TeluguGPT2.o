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

def format_memory_context(memory):
    """Format memory into a clear, structured context string"""
    context_parts = []
    for entity, details in memory.items():
        if isinstance(details, dict):
            properties = [f"{k} is {v}" for k, v in details.items()]
            context_parts.append(f"The {entity} {' and '.join(properties)}")
    return " ".join(context_parts)

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

        # Format memory context in a more structured way
        memory_context = format_memory_context(session["memory"])
        
        # Enhanced system prompt with explicit memory usage instruction
        system_prompt = f"""You are a helpful assistant that responds only in Telugu with correct grammar.
        IMPORTANT STORED INFORMATION: {memory_context}
        You MUST use this stored information to answer questions about previously mentioned details.
        When asked about any information that matches the stored details above, use that information in your response.
        Answer the query appropriately without translating the question itself."""

        # Build messages list
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text}
        ]

        # Add a reminder message if the query might be about stored information
        if any(keyword in input_text.lower() for keyword in ["what", "tell", "what is", "my"]):
            memory_reminder = {"role": "system", "content": f"Remember to check and use this stored information: {memory_context}"}
            messages.insert(1, memory_reminder)

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
        
        # Limit chat history length
        if len(session["chat_history"]) > 20:
            session["chat_history"] = session["chat_history"][-20:]
        
        session.modified = True

        return jsonify({
            "response": response_text,
            "memory": session["memory"]  # Return current memory state for debugging
        })

    except Exception as e:
        print(f"Error in ask route: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)  
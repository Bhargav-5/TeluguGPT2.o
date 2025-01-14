import openai
import os
from openai import OpenAI
from flask import Flask,render_template,request,jsonify
from flask_cors import CORS

os.environ["OPENAI_API_KEY"] = os.getenv('API_KEY')

app = Flask(__name__)
CORS(app)
client = OpenAI()

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        input_text = data.get("query", "")

        if not input_text:
            return jsonify({"error": "No input provided"}), 400
        # Define the system and user messages
        prompt = f"Answer the user's query only in Telugu which is with correct grammar {input_text} do not translate that query and send response just analyze the user query and answer to it accordingly finally remember all the chats"
    
        # Call the ChatGPT API
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the content of the response
        response_text = completion.choices[0].message.content.strip()
        # print("Response:", response_text) 

        # Save the response to a file
        # with open("demofile.txt", "w") as f:
        #     f.write(response_text)

        # Return the response
        return jsonify({"response": response_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# def generate_Telugu_Response(input_text):
#     print("IN GENERATE RESPONSE . . . . .")
    
# print(generate_Telugu_Response(text))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) 
    app.run(host='0.0.0.0', port=port, debug=True)

# original
import openai
import os
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from openai import OpenAI

os.environ["OPENAI_API_KEY"] = os.getenv('API_KEY')
app = Flask(__name__)
CORS(app)
client = OpenAI()

@app.route('/get_telugu_response', methods=['GET', 'POST'])
def ask():
    try:
        data = request.get_json()
        input_text = data.get("message", "")

        if not input_text:
            return jsonify({"error": "No input provided"}), 400

        prompt = f'''
                    This is the user query {input_text}. Reply to this user query in telugu
                    only and give me the response back and only the response, which is in marked down
                    and only use double * in the output wherever necessary no hashes.
                  '''

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = completion.choices[0].message.content.strip()

        with open("demofile.txt", "w") as f:
            f.write(response_text)

        return jsonify({"response": response_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) 
    app.run(host='0.0.0.0', port=port, debug=True)

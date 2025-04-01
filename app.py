from flask import Flask, request, jsonify
import send

app = Flask(__name__)

@app.route('/send-emoji', methods=['POST'])
def handle_send_emoji():
    data = request.json
    emoji = data.get("emoji", "🙂")
    result = send.send_emoji(emoji) 
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
    

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['POST'])
def receive_data():
    data = request.get_json()
    print("Received data:", data)
    return jsonify({"status": "success", "data": data}), 200

if __name__ == '__main__':
    print("Flask server starting...")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

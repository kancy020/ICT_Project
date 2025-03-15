from flask import Flask, Response
from flask import request as flask_request

#setting up flask file
app = Flask(__name__)

#get method to produce a response on the url 
@app.route("/", methods=['GET'])
def hello():
    return Response("Hello, World!"), 200

#post method to test the generated token
@app.route('/verify', methods=['POST'])
def inbound():
    """
    testing to see if token worked
    """
    #payload from flask handles the JSON file request
    payload = flask_request.get_json()

    #once the challenge request it recieved repond to successfully initialise request
    if payload and 'challenge' in payload:
        return Response(payload['challenge']), 200
    
    return Response("Missing challenge key", status=400)

if __name__ == '__main__':
    app.run(debug=True)
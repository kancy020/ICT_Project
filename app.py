from flask import Flask

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
    if payload:
        return Response(payload['challenge']), 200
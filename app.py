from flask import Flask, Response
from flask import request as flask_request

#setting up flask file
app = Flask(__name__)

#get method to produce a response on the url 
@app.route('/slack/command', methods=['POST'])
def command():
    data = flask_request.form
    return Response("command is recieved", status=200)

if __name__ == '__main__':
    app.run(debug=True)
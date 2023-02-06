from flask import Flask, request, jsonify
from flask_cors import CORS
from toppick import toppick_detect

app = Flask(__name__)
app.config['DEBUG'] = True
CORS(app)

@app.route("/toppicks", methods=['GET', 'POST'])
def toppick_show():
    option = request.json
    print(option)
    result = { 'stocks' : 'samsung'}
    
    return jsonify(result)

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
from app import getApp
from flask import Flask
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
app.secret_key = 'cheetos'
app.config['SESSION_COOKIE_NAME'] = 'tu_sesion'

getApp(app)

if __name__ == '__main__':

    app.run(debug=True, host='0.0.0.0', port=5000)


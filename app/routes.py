from flask import Blueprint, render_template

# Define el blueprint
main = Blueprint('main', __name__)

# Define las rutas
@main.route('/')
def index():
    print("Hola pendejos soy el anticristo 2006")
    return render_template('index.html')


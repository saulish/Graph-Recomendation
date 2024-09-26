from flask import Blueprint, render_template, jsonify, request, redirect, url_for, session
from app.conect import login, getToken, refrescarToken, getPlaylist, getDatos

# Define el blueprint
main = Blueprint('main', __name__)

# Define las rutas
@main.route('/')
def index():
    print("Hola pendejos soy el anticristo 2006")
    return render_template('index.html')

@main.route('/menu')
def menu():
    # Aquí renderizas la página del menú
    return render_template('menu.html')

@main.route('/saludar')
def saludo():
    
    return jsonify({'message': f'Hola Saul!'})


@main.route('/login')
def iniciar():
    url=login()
    return redirect(url)
    

@main.route('/callback')
def callback():
    code = request.args.get('code')
    
    token_info =getToken(code)

    if not token_info:
        return redirect(url_for('index'))
    refrescarToken(token_info)

    return redirect(url_for('main.menu'))


@main.route('/playlists')
def playlists():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('index'))  
    playlists = getPlaylist(token_info)
    return jsonify(playlists)  


@main.route('/analizarPlyalist')
def analizar():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('index'))   
    id = request.args.get('id')
    print(f'ID: {id}')
    songs,datos=getDatos(token_info,id)
    return jsonify({'songs': songs, 'datos': datos})
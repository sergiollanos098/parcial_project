from flask import Flask, jsonify, request, g
from flasgger import Swagger
from flask_cors import CORS
import mysql.connector
import os

app = Flask(__name__)
CORS(app)

# --- Swagger Config ---
app.config['SWAGGER'] = {
    'title': 'Usuarios API (con direcciones) - CRUD completo',
    'uiversion': 3
}
Swagger(app)

# --- MySQL Config (desde variables de entorno) ---
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASS = os.getenv("MYSQL_PASS", "")
MYSQL_DB   = os.getenv("MYSQL_DB", "db_usuarios")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))

# ---------- DB helpers ----------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASS,
            database=MYSQL_DB,
            port=MYSQL_PORT
        )
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ---------- USERS ----------
@app.route('/users', methods=['GET'])
def get_users():
    """Obtener lista de usuarios con sus direcciones"""
    limit = int(request.args.get('limit', 20))
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id,name,email FROM users ORDER BY id DESC LIMIT %s", (limit,))
    users = cur.fetchall()

    for u in users:
        cur2 = db.cursor(dictionary=True)
        cur2.execute("SELECT id,city,street FROM addresses WHERE user_id=%s", (u['id'],))
        u['addresses'] = cur2.fetchall()
    return jsonify(users)

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Obtener un usuario con sus direcciones"""
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id,name,email FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404
    cur.execute("SELECT id,city,street FROM addresses WHERE user_id=%s", (user_id,))
    user['addresses'] = cur.fetchall()
    return jsonify(user)

@app.route('/users', methods=['POST'])
def add_user():
    """Crear un nuevo usuario"""
    data = request.get_json() or {}
    if not data.get('name') or not data.get('email'):
        return jsonify({"error": "name and email required"}), 400
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO users (name,email) VALUES (%s,%s)", (data['name'], data['email']))
    db.commit()
    return jsonify({"id": cur.lastrowid, "name": data['name'], "email": data['email']}), 201

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Actualizar usuario"""
    data = request.get_json() or {}
    if not data:
        return jsonify({"error": "body required"}), 400
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE users SET name=%s, email=%s WHERE id=%s", (data.get('name'), data.get('email'), user_id))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"status": "updated"})

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Eliminar usuario y sus direcciones"""
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM addresses WHERE user_id=%s", (user_id,))
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"status": "deleted"})

# --------------- ADDRESSES CRUD ---------------
@app.route('/addresses', methods=['GET'])
def list_addresses():
    """Listar direcciones"""
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', default=50, type=int)
    offset = request.args.get('offset', default=0, type=int)
    db = get_db()
    cur = db.cursor(dictionary=True)
    if user_id:
        cur.execute("SELECT id,user_id,city,street FROM addresses WHERE user_id=%s LIMIT %s OFFSET %s", (user_id, limit, offset))
    else:
        cur.execute("SELECT id,user_id,city,street FROM addresses LIMIT %s OFFSET %s", (limit, offset))
    return jsonify(cur.fetchall())

@app.route('/addresses/<int:address_id>', methods=['GET'])
def get_address(address_id):
    """Obtener dirección por id"""
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id,user_id,city,street FROM addresses WHERE id=%s", (address_id,))
    a = cur.fetchone()
    if not a:
        return jsonify({"error": "Address not found"}), 404
    return jsonify(a)

@app.route('/addresses', methods=['POST'])
def create_address():
    """Crear dirección"""
    data = request.get_json() or {}
    if not data.get('user_id'):
        return jsonify({"error": "user_id required"}), 400
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id FROM users WHERE id=%s", (data['user_id'],))
    if not cur.fetchone():
        return jsonify({"error": "User not found"}), 400
    cur = db.cursor()
    cur.execute("INSERT INTO addresses (user_id,city,street) VALUES (%s,%s,%s)",
                (data['user_id'], data.get('city'), data.get('street')))
    db.commit()
    return jsonify({"id": cur.lastrowid, "user_id": data['user_id'], "city": data.get('city'), "street": data.get('street')}), 201

@app.route('/addresses/<int:address_id>', methods=['PUT'])
def update_address(address_id):
    """Actualizar dirección"""
    data = request.get_json() or {}
    if not data:
        return jsonify({"error": "body required"}), 400
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE addresses SET city=%s, street=%s WHERE id=%s",
                (data.get('city'), data.get('street'), address_id))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Address not found"}), 404
    return jsonify({"status": "updated"})

@app.route('/addresses/<int:address_id>', methods=['DELETE'])
def delete_address(address_id):
    """Eliminar dirección"""
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM addresses WHERE id=%s", (address_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Address not found"}), 404
    return jsonify({"status": "deleted"})

# ------------ root/info --------------
@app.route('/')
def index():
    return jsonify({
        "status": "ok",
        "swagger_ui": "/apidocs",
        "tables": ["users", "addresses"],
        "relations": "1:N (user -> addresses)"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)


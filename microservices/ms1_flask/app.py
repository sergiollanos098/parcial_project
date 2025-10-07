from flask import Flask, jsonify, request, g
import sqlite3, os
from flasgger import Swagger

app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'Usuarios API (con direcciones) - CRUD completo',
    'uiversion': 3
}
Swagger(app)

DB = 'users.db'


# ---------- DB helpers ----------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# ---------- Init (tables + seed) ----------
@app.route('/init', methods=['GET'])
def init():
    """
    Inicializa las tablas users y addresses con datos de ejemplo.
    ---
    responses:
      200:
        description: Inicialización completada o ya existe
    """
    if not os.path.exists(DB):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
        """)
        c.execute("""
            CREATE TABLE addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                city TEXT,
                street TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        # seed
        for i in range(1, 51):
            c.execute('INSERT INTO users (name,email) VALUES (?,?)',
                      (f'User{i}', f'user{i}@example.com'))
            c.execute('INSERT INTO addresses (user_id, city, street) VALUES (?,?,?)',
                      (i, f'City{i}', f'Street {i}'))
        conn.commit()
        conn.close()
        return jsonify({"status": "initialized", "users": 50}), 200
    return jsonify({"status": "already"}), 200


# ---------------- USERS (kept) ----------------
@app.route('/users', methods=['GET'])
def get_users():
    """
    Obtener lista de usuarios con sus direcciones (limit opcional)
    ---
    parameters:
      - name: limit
        in: query
        type: integer
        required: false
    responses:
      200:
        description: Lista de usuarios con direcciones
    """
    limit = int(request.args.get('limit', 20))
    db = get_db()
    cur = db.execute('SELECT id,name,email FROM users ORDER BY id DESC LIMIT ?', (limit,))
    users = []
    for u in cur.fetchall():
        cur2 = db.execute('SELECT id,city,street FROM addresses WHERE user_id=?', (u['id'],))
        addresses = [{"id": a["id"], "city": a["city"], "street": a["street"]} for a in cur2.fetchall()]
        users.append({"id": u["id"], "name": u["name"], "email": u["email"], "addresses": addresses})
    return jsonify(users)


@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Obtener un usuario y sus direcciones
    ---
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Usuario con direcciones
    """
    db = get_db()
    cur = db.execute('SELECT id,name,email FROM users WHERE id=?', (user_id,))
    user = cur.fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404
    cur2 = db.execute('SELECT id,city,street FROM addresses WHERE user_id=?', (user_id,))
    addresses = [{"id": a["id"], "city": a["city"], "street": a["street"]} for a in cur2.fetchall()]
    return jsonify({"id": user["id"], "name": user["name"], "email": user["email"], "addresses": addresses})


@app.route('/users', methods=['POST'])
def add_user():
    """
    Crear un nuevo usuario
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            name:
              type: string
            email:
              type: string
    responses:
      201:
        description: Usuario creado
    """
    data = request.get_json() or {}
    if not data.get('name') or not data.get('email'):
        return jsonify({"error": "name and email required"}), 400
    db = get_db()
    cur = db.execute('INSERT INTO users (name,email) VALUES (?,?)', (data['name'], data['email']))
    db.commit()
    return jsonify({"id": cur.lastrowid, "name": data['name'], "email": data['email']}), 201


@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Actualizar usuario
    ---
    parameters:
      - name: user_id
        in: path
        type: integer
      - name: body
        in: body
        required: true
        schema:
          properties:
            name: {type: string}
            email: {type: string}
    responses:
      200:
        description: Usuario actualizado
    """
    data = request.get_json() or {}
    if not data:
        return jsonify({"error": "body required"}), 400
    db = get_db()
    cur = db.execute('UPDATE users SET name=?, email=? WHERE id=?', (data.get('name'), data.get('email'), user_id))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"status": "updated"})


@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Eliminar usuario y sus direcciones
    ---
    parameters:
      - name: user_id
        in: path
        type: integer
    responses:
      200:
        description: Usuario eliminado
    """
    db = get_db()
    db.execute('DELETE FROM addresses WHERE user_id=?', (user_id,))
    cur = db.execute('DELETE FROM users WHERE id=?', (user_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"status": "deleted"})


# --------------- ADDRESSES CRUD ---------------

@app.route('/addresses', methods=['GET'])
def list_addresses():
    """
    Listar direcciones
    ---
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
      - name: limit
        in: query
        type: integer
        required: false
      - name: offset
        in: query
        type: integer
        required: false
    responses:
      200:
        description: Lista de direcciones
    """
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', default=50, type=int)
    offset = request.args.get('offset', default=0, type=int)
    db = get_db()
    if user_id:
        cur = db.execute('SELECT id,user_id,city,street FROM addresses WHERE user_id=? LIMIT ? OFFSET ?', (user_id, limit, offset))
    else:
        cur = db.execute('SELECT id,user_id,city,street FROM addresses LIMIT ? OFFSET ?', (limit, offset))
    addresses = [{"id": r["id"], "user_id": r["user_id"], "city": r["city"], "street": r["street"]} for r in cur.fetchall()]
    return jsonify(addresses)


@app.route('/addresses/<int:address_id>', methods=['GET'])
def get_address(address_id):
    """
    Obtener dirección por id
    ---
    parameters:
      - name: address_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Dirección encontrada
    """
    db = get_db()
    cur = db.execute('SELECT id,user_id,city,street FROM addresses WHERE id=?', (address_id,))
    a = cur.fetchone()
    if not a:
        return jsonify({"error": "Address not found"}), 404
    return jsonify({"id": a["id"], "user_id": a["user_id"], "city": a["city"], "street": a["street"]})


@app.route('/addresses', methods=['POST'])
def create_address():
    """
    Crear dirección para un usuario
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            user_id: {type: integer}
            city: {type: string}
            street: {type: string}
    responses:
      201:
        description: Dirección creada
    """
    data = request.get_json() or {}
    if not data.get('user_id'):
        return jsonify({"error": "user_id required"}), 400
    db = get_db()
    # check user exists
    u = db.execute('SELECT id FROM users WHERE id=?', (data['user_id'],)).fetchone()
    if not u:
        return jsonify({"error": "User not found"}), 400
    cur = db.execute('INSERT INTO addresses (user_id,city,street) VALUES (?,?,?)',
                     (data['user_id'], data.get('city'), data.get('street')))
    db.commit()
    return jsonify({"id": cur.lastrowid, "user_id": data['user_id'], "city": data.get('city'), "street": data.get('street')}), 201


@app.route('/addresses/<int:address_id>', methods=['PUT'])
def update_address(address_id):
    """
    Actualizar dirección
    ---
    parameters:
      - name: address_id
        in: path
        type: integer
      - name: body
        in: body
        schema:
          properties:
            city: {type: string}
            street: {type: string}
    responses:
      200:
        description: Dirección actualizada
    """
    data = request.get_json() or {}
    if not data:
        return jsonify({"error": "body required"}), 400
    db = get_db()
    # get existing
    a = db.execute('SELECT id FROM addresses WHERE id=?', (address_id,)).fetchone()
    if not a:
        return jsonify({"error": "Address not found"}), 404
    # update only provided fields
    cur = db.execute('UPDATE addresses SET city=?, street=? WHERE id=?',
                     (data.get('city'), data.get('street'), address_id))
    db.commit()
    return jsonify({"status": "updated"})


@app.route('/addresses/<int:address_id>', methods=['DELETE'])
def delete_address(address_id):
    """
    Eliminar dirección
    ---
    parameters:
      - name: address_id
        in: path
        type: integer
    responses:
      200:
        description: Dirección eliminada
    """
    db = get_db()
    cur = db.execute('DELETE FROM addresses WHERE id=?', (address_id,))
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

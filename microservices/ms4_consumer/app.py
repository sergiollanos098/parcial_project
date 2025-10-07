from flask import Flask, jsonify, request
import requests, os
from flasgger import Swagger

app = Flask(__name__)
app.config["SWAGGER"] = {"title": "Consumer Multi-Entorno", "uiversion": 3}
Swagger(app)

# ---- Direcciones por entorno ----
ENV_CONFIG = {
    "prod1": {
        "MS1": os.getenv("MS1_PROD1", "http://172.31.10.11:5001"),
        "MS2": os.getenv("MS2_PROD1", "http://172.31.10.11:5002"),
        "MS3": os.getenv("MS3_PROD1", "http://172.31.10.11:5003"),
    },
    "prod2": {
        "MS1": os.getenv("MS1_PROD2", "http://172.31.11.11:5001"),
        "MS2": os.getenv("MS2_PROD2", "http://172.31.11.11:5002"),
        "MS3": os.getenv("MS3_PROD2", "http://172.31.11.11:5003"),
    },
}

@app.get("/")
def index():
    return jsonify({
        "status": "ok",
        "swagger_ui": "/apidocs",
        "available_envs": list(ENV_CONFIG.keys())
    })

@app.get("/aggregate")
def aggregate():
    """
    Combina datos de los 3 MS de un entorno (Prod1 o Prod2)
    ---
    parameters:
      - name: env
        in: query
        type: string
        required: false
        description: Entorno a usar (prod1 o prod2)
    responses:
      200:
        description: Datos agregados del entorno seleccionado
    """
    env = request.args.get("env", "prod1")
    cfg = ENV_CONFIG.get(env)
    if not cfg:
        return jsonify({"error": "Entorno inválido"}), 400

    try:
        users = requests.get(f"{cfg['MS1']}/users", timeout=5).json()
        patients = requests.get(f"{cfg['MS2']}/patients", timeout=5).json()
        exams = requests.get(f"{cfg['MS3']}/exams", timeout=5).json()

        return jsonify({
            "environment": env,
            "users_sample": users[:3],
            "patients_sample": patients[:3],
            "exams_sample": exams[:3],
            "status": "aggregated"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/compare")
def compare():
    """
    Compara conteos de registros entre Prod1 y Prod2
    ---
    responses:
      200:
        description: Diferencias entre entornos
    """
    result = {}
    for env, cfg in ENV_CONFIG.items():
        try:
            u = len(requests.get(f"{cfg['MS1']}/users", timeout=5).json())
            p = len(requests.get(f"{cfg['MS2']}/patients", timeout=5).json())
            e = len(requests.get(f"{cfg['MS3']}/exams", timeout=5).json())
            result[env] = {"users": u, "patients": p, "exams": e}
        except Exception as err:
            result[env] = {"error": str(err)}

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004)

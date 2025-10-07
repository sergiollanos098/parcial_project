from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = FastAPI(title="Pacientes API", description="Microservicio de gestión de pacientes y citas médicas", version="1.0")

# ---------- Configuración BD ----------
DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASS", "postgres"),
    "dbname": os.getenv("PG_DB", "medical_db"),
    "port": os.getenv("PG_PORT", 5432),
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


# ---------- Modelos Pydantic ----------
class Patient(BaseModel):
    name: str
    age: int


class Appointment(BaseModel):
    patient_id: int
    date: str
    reason: str


# ---------- Inicialización ----------
@app.get("/init")
def init_db():
    """Crea las tablas patients y appointments con datos de ejemplo"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            age INT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id SERIAL PRIMARY KEY,
            patient_id INT REFERENCES patients(id) ON DELETE CASCADE,
            date VARCHAR(50),
            reason VARCHAR(200)
        )
    """)
    # Insertar pacientes de ejemplo solo si está vacío
    cur.execute("SELECT COUNT(*) FROM patients")
    if cur.fetchone()["count"] == 0:
        for i in range(1, 51):
            cur.execute("INSERT INTO patients (name, age) VALUES (%s,%s)", (f"Patient{i}", 20 + (i % 60)))
            cur.execute("INSERT INTO appointments (patient_id, date, reason) VALUES (%s,%s,%s)",
                        (i, f"2025-10-{(i%28)+1:02d}", f"Consulta general {i}"))
    conn.commit()
    conn.close()
    return {"status": "initialized"}


# ---------- CRUD Patients ----------
@app.get("/patients")
def list_patients(limit: int = 20):
    """Lista pacientes con sus citas médicas"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients ORDER BY id ASC LIMIT %s", (limit,))
    patients = cur.fetchall()
    for p in patients:
        cur.execute("SELECT id,date,reason FROM appointments WHERE patient_id=%s", (p["id"],))
        p["appointments"] = cur.fetchall()
    conn.close()
    return patients


@app.get("/patients/{patient_id}")
def get_patient(patient_id: int):
    """Obtiene un paciente por ID"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients WHERE id=%s", (patient_id,))
    p = cur.fetchone()
    if not p:
        raise HTTPException(404, "Paciente no encontrado")
    cur.execute("SELECT id,date,reason FROM appointments WHERE patient_id=%s", (patient_id,))
    p["appointments"] = cur.fetchall()
    conn.close()
    return p


@app.post("/patients", status_code=201)
def create_patient(patient: Patient):
    """Crea un nuevo paciente"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO patients (name, age) VALUES (%s,%s) RETURNING *", (patient.name, patient.age))
    new_patient = cur.fetchone()
    conn.commit()
    conn.close()
    return new_patient


@app.put("/patients/{patient_id}")
def update_patient(patient_id: int, patient: Patient):
    """Actualiza los datos de un paciente"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE patients SET name=%s, age=%s WHERE id=%s RETURNING *",
                (patient.name, patient.age, patient_id))
    updated = cur.fetchone()
    conn.commit()
    conn.close()
    if not updated:
        raise HTTPException(404, "Paciente no encontrado")
    return updated


@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: int):
    """Elimina un paciente y sus citas"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM patients WHERE id=%s RETURNING id", (patient_id,))
    deleted = cur.fetchone()
    conn.commit()
    conn.close()
    if not deleted:
        raise HTTPException(404, "Paciente no encontrado")
    return {"status": "deleted", "id": deleted["id"]}


# ---------- CRUD Appointments ----------
@app.get("/appointments")
def list_appointments(limit: int = 50):
    """Lista todas las citas"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id,a.patient_id,a.date,a.reason,p.name
        FROM appointments a
        JOIN patients p ON a.patient_id=p.id
        ORDER BY a.date ASC LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


@app.get("/appointments/{appointment_id}")
def get_appointment(appointment_id: int):
    """Obtiene una cita específica"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id,a.patient_id,a.date,a.reason,p.name
        FROM appointments a
        JOIN patients p ON a.patient_id=p.id
        WHERE a.id=%s
    """, (appointment_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Cita no encontrada")
    return row


@app.post("/appointments", status_code=201)
def create_appointment(ap: Appointment):
    """Crea una nueva cita médica"""
    conn = get_conn()
    cur = conn.cursor()
    # verificar que el paciente exista
    cur.execute("SELECT id FROM patients WHERE id=%s", (ap.patient_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(400, "Paciente no existe")
    cur.execute("INSERT INTO appointments (patient_id,date,reason) VALUES (%s,%s,%s) RETURNING *",
                (ap.patient_id, ap.date, ap.reason))
    new_ap = cur.fetchone()
    conn.commit()
    conn.close()
    return new_ap


@app.put("/appointments/{appointment_id}")
def update_appointment(appointment_id: int, ap: Appointment):
    """Actualiza una cita médica"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE appointments SET date=%s, reason=%s WHERE id=%s RETURNING *",
                (ap.date, ap.reason, appointment_id))
    updated = cur.fetchone()
    conn.commit()
    conn.close()
    if not updated:
        raise HTTPException(404, "Cita no encontrada")
    return updated


@app.delete("/appointments/{appointment_id}")
def delete_appointment(appointment_id: int):
    """Elimina una cita médica"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM appointments WHERE id=%s RETURNING id", (appointment_id,))
    deleted = cur.fetchone()
    conn.commit()
    conn.close()
    if not deleted:
        raise HTTPException(404, "Cita no encontrada")
    return {"status": "deleted", "id": deleted["id"]}


@app.get("/")
def index():
    return {
        "status": "ok",
        "swagger_ui": "/docs",
        "redoc": "/redoc",
        "tables": ["patients", "appointments"],
        "relation": "1:N (patient -> appointments)"
    }

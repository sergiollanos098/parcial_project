const express = require("express");
const { MongoClient, ObjectId } = require("mongodb");
const swaggerUi = require("swagger-ui-express");
const swaggerJsdoc = require("swagger-jsdoc");
const app = express();
app.use(express.json());

const PORT = 5003;
const MONGO = process.env.MONGO_URI || "mongodb://172.31.22.15:27017"; // IP privada MV-BD
const DBNAME = "clinicdb";

let db;

// ---------- Conexión Mongo ----------
MongoClient.connect(MONGO, { useUnifiedTopology: true })
  .then((client) => {
    db = client.db(DBNAME);
    console.log("✅ Conectado a MongoDB");
  })
  .catch((err) => console.error("❌ Error Mongo:", err));

// ---------- Swagger Config ----------
const options = {
  definition: {
    openapi: "3.0.0",
    info: {
      title: "Microservicio de Exámenes y Estudiantes",
      version: "1.0.0",
      description:
        "API Node + Express + MongoDB para gestión de exámenes clínicos y estudiantes",
    },
    servers: [{ url: `http://localhost:${PORT}` }],
  },
  apis: ["./app.js"],
};
const specs = swaggerJsdoc(options);
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(specs));

// ---------- Rutas ----------
/**
 * @swagger
 * /init:
 *   get:
 *     summary: Inicializa las colecciones con datos de prueba
 *     responses:
 *       200:
 *         description: Datos insertados
 */
app.get("/init", async (req, res) => {
  try {
    const examsCol = db.collection("exams");
    const studentsCol = db.collection("students");

    await examsCol.deleteMany({});
    await studentsCol.deleteMany({});

    const exams = [];
    for (let i = 1; i <= 50; i++) {
      exams.push({
        type: "exam" + (i % 10),
        specialty: "spec" + (i % 5),
        date: `2025-10-${(i % 28) + 1}`,
      });
    }
    const examResult = await examsCol.insertMany(exams);

    const students = [];
    for (let i = 1; i <= 50; i++) {
      students.push({
        name: `Student${i}`,
        age: 18 + (i % 10),
        exam_id: examResult.insertedIds[i - 1],
      });
    }
    await studentsCol.insertMany(students);

    res.json({ status: "ok", exams: 50, students: 50 });
  } catch (e) {
    res.json({ error: e.toString() });
  }
});

// =================== EXAMS CRUD ===================
/**
 * @swagger
 * /exams:
 *   get:
 *     summary: Lista todos los exámenes
 *     responses:
 *       200:
 *         description: Lista de exámenes
 */
app.get("/exams", async (req, res) => {
  try {
    const docs = await db.collection("exams").find({}).limit(50).toArray();
    res.json(docs);
  } catch (e) {
    res.status(500).json({ error: e.toString() });
  }
});

/**
 * @swagger
 * /exams/{id}:
 *   get:
 *     summary: Obtiene un examen por ID
 */
app.get("/exams/:id", async (req, res) => {
  try {
    const doc = await db
      .collection("exams")
      .findOne({ _id: new ObjectId(req.params.id) });
    if (!doc) return res.status(404).json({ error: "Exam not found" });
    res.json(doc);
  } catch (e) {
    res.status(400).json({ error: e.toString() });
  }
});

/**
 * @swagger
 * /exams:
 *   post:
 *     summary: Crea un nuevo examen
 */
app.post("/exams", async (req, res) => {
  try {
    const { type, specialty, date } = req.body;
    const result = await db
      .collection("exams")
      .insertOne({ type, specialty, date });
    res.status(201).json({ id: result.insertedId, type, specialty, date });
  } catch (e) {
    res.status(400).json({ error: e.toString() });
  }
});

/**
 * @swagger
 * /exams/{id}:
 *   put:
 *     summary: Actualiza un examen existente
 */
app.put("/exams/:id", async (req, res) => {
  try {
    const { type, specialty, date } = req.body;
    const result = await db
      .collection("exams")
      .updateOne(
        { _id: new ObjectId(req.params.id) },
        { $set: { type, specialty, date } }
      );
    if (result.matchedCount === 0)
      return res.status(404).json({ error: "Exam not found" });
    res.json({ status: "updated" });
  } catch (e) {
    res.status(400).json({ error: e.toString() });
  }
});

/**
 * @swagger
 * /exams/{id}:
 *   delete:
 *     summary: Elimina un examen
 */
app.delete("/exams/:id", async (req, res) => {
  try {
    const result = await db
      .collection("exams")
      .deleteOne({ _id: new ObjectId(req.params.id) });
    if (result.deletedCount === 0)
      return res.status(404).json({ error: "Exam not found" });
    res.json({ status: "deleted" });
  } catch (e) {
    res.status(400).json({ error: e.toString() });
  }
});

// =================== STUDENTS CRUD ===================
/**
 * @swagger
 * /students:
 *   get:
 *     summary: Lista todos los estudiantes
 */
app.get("/students", async (req, res) => {
  try {
    const docs = await db.collection("students").find({}).limit(50).toArray();
    res.json(docs);
  } catch (e) {
    res.status(500).json({ error: e.toString() });
  }
});

/**
 * @swagger
 * /students/{id}:
 *   get:
 *     summary: Obtiene un estudiante por ID
 */
app.get("/students/:id", async (req, res) => {
  try {
    const doc = await db
      .collection("students")
      .findOne({ _id: new ObjectId(req.params.id) });
    if (!doc) return res.status(404).json({ error: "Student not found" });
    res.json(doc);
  } catch (e) {
    res.status(400).json({ error: e.toString() });
  }
});

/**
 * @swagger
 * /students:
 *   post:
 *     summary: Crea un nuevo estudiante
 */
app.post("/students", async (req, res) => {
  try {
    const { name, age, exam_id } = req.body;
    const result = await db
      .collection("students")
      .insertOne({ name, age, exam_id });
    res.status(201).json({ id: result.insertedId, name, age, exam_id });
  } catch (e) {
    res.status(400).json({ error: e.toString() });
  }
});

/**
 * @swagger
 * /students/{id}:
 *   put:
 *     summary: Actualiza un estudiante
 */
app.put("/students/:id", async (req, res) => {
  try {
    const { name, age, exam_id } = req.body;
    const result = await db
      .collection("students")
      .updateOne(
        { _id: new ObjectId(req.params.id) },
        { $set: { name, age, exam_id } }
      );
    if (result.matchedCount === 0)
      return res.status(404).json({ error: "Student not found" });
    res.json({ status: "updated" });
  } catch (e) {
    res.status(400).json({ error: e.toString() });
  }
});

/**
 * @swagger
 * /students/{id}:
 *   delete:
 *     summary: Elimina un estudiante
 */
app.delete("/students/:id", async (req, res) => {
  try {
    const result = await db
      .collection("students")
      .deleteOne({ _id: new ObjectId(req.params.id) });
    if (result.deletedCount === 0)
      return res.status(404).json({ error: "Student not found" });
    res.json({ status: "deleted" });
  } catch (e) {
    res.status(400).json({ error: e.toString() });
  }
});

// ---------- Root ----------
app.get("/", (req, res) => {
  res.json({
    status: "ok",
    swagger_ui: "/api-docs",
    collections: ["exams", "students"],
    relation: "1:N (exam -> students)",
  });
});

app.listen(PORT, () => console.log("🧩 ms3 listening on port", PORT));

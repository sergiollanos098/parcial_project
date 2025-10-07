# Proyecto Parcial - Scaffold (Entregable rápido y económico)

## Contenido
- 5 microservicios en `microservices/` (ms1..ms5)
- `docker-compose.yml` para ejecutar todo en una máquina (o en dos máquinas si sigues el diagrama)
- `nginx/` con configuración para exponer rutas /ms1, /ms2, /ms3, /ms4, /ms5
- `frontend/index.html` simple que consume las APIs a través de nginx
- `data_ingesta/` script para ingesta de datos (placeholder)

## Recomendación económica para AWS (usar free tier)
1. Crear 2 EC2 `t2.micro` (Amazon Linux 2).
2. En MV1: clonar este repo, instalar docker & docker-compose, y levantar stack:
   ```bash
   docker-compose up --build -d
   ```
   Esto levantará nginx + ms1..ms5 + local mongo. nginx expone puerto 80.
3. En MV2: puedes levantar otra copia y usarla para alta disponibilidad o solo para contenedores de ingesta.
4. Inicializar bases de datos:
   - Visitar `http://<EC2_IP>/ms1/init` y `http://<EC2_IP>/ms2/init` y `http://<EC2_IP>/ms3/init` para poblar datos de ejemplo.
5. Ingesta a S3:
   - Crea un bucket S3.
   - Corre el contenedor `data_ingesta` configurando variables `API` y AWS creds. (README detalla cómo usar boto3)
6. Frontend:
   - Puedes hospedar `frontend/index.html` en AWS Amplify (conectar a GitHub) o simplemente servirlo desde nginx (copiar a /usr/share/nginx/html).

## Cómo documentar rapido (Swagger + pruebas)
- Cada servicio expone endpoints básicos (/init y /resource). Para cumplir la rúbrica, añade `swagger.yaml` o documentación mínima en el README de cada microservice.
- Insertar masivamente 20,000 registros: usar un script con `Faker` (puedo generarlo si quieres).

## Nota sobre DBs para rúbrica
- ms1: SQLite (SQL)
- ms2: SQLite (SQL) - distinta DB file
- ms3: MongoDB (NoSQL) - usa local mongo o MongoDB Atlas free tier
- ms4: no DB (consumer)
- ms5: analytics (mocked; reemplazar por consultas Athena cuando hagas Glue + S3)

## Archivos importantes
- docker-compose.yml
- nginx/nginx.conf
- microservices/*

---
Siguiente paso: ¿Quieres que genere también:
1) El script `faker_insert.py` para crear 20,000 registros por BD y los agregue automáticamente? (lo hago ahora)  
2) Un `deploy.sh` que automatice instalación de Docker en EC2 y arranque del stack? (lo hago ahora)
3) Un zip descargable del proyecto (ya generado por este notebook)?

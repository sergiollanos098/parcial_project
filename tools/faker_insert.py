# faker_insert.py - generate large fake datasets into sqlite and mongo for the project
from faker import Faker
import sqlite3, os
from pymongo import MongoClient

fake = Faker()

# populate sqlite users.db
conn = sqlite3.connect('microservices/ms1_flask/users.db')
c = conn.cursor()
try:
    c.execute('CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT)')
except:
    pass
for i in range(1,20001):
    c.execute('INSERT INTO users (name,email) VALUES (?,?)', (fake.name(), fake.email()))
conn.commit()
conn.close()

# populate medical.db
conn2 = sqlite3.connect('microservices/ms2_fastapi/medical.db')
c2 = conn2.cursor()
try:
    c2.execute('CREATE TABLE patients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER)')
except:
    pass
for i in range(1,20001):
    c2.execute('INSERT INTO patients (name,age) VALUES (?,?)', (fake.name(), fake.random_int(1,90)))
conn2.commit()
conn2.close()

# populate mongo (if accessible)
try:
    client = MongoClient('mongodb://localhost:27017')
    db = client['clinicdb']
    col = db['exams']
    bulk = []
    for i in range(1,20001):
        bulk.append({'exam_id':i, 'type': 'exam'+str(i%10), 'specialty':'spec'+str(i%7)})
        if len(bulk)>=1000:
            col.insert_many(bulk); bulk=[]
    if bulk: col.insert_many(bulk)
    print('mongo OK')
except Exception as e:
    print('mongo skipped', e)

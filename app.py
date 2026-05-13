from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import mongomock
import os
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'europa_peace_secret_2026'
socketio = SocketIO(app, cors_allowed_origins="*")

client = None
db = None

def connect_to_db():
    global client, db
    if client is None:
        try:
            # Try to connect to a real MongoDB
            client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
            client.admin.command('ismaster')
            print("Connected to MongoDB - Europa Peace System")
        except ConnectionFailure:
            print("Real MongoDB not found on port 27017. Falling back to mongomock (in-memory).")
            client = mongomock.MongoClient()
        
        db = client["europa_peace_db"]
        
        # Seed initial data if empty
        if db.countries.count_documents({}) == 0:
            seed_data(db)
            
    return db

def seed_data(database):
    print("Seeding initial data...")
    # Add a few historical states with rudimentary polygons
    countries = [
        {
            "name": "France",
            "isHistorical": True,
            "graphicShape": [[48.8, 2.3], [43.3, 5.4], [44.8, -0.6]],
            "borders": [
                {"name": "Franco-Spanish Border", "curveCoordinates": [[43.3, 5.4], [42.8, 0.6], [43.3, -1.7]], "lengthKm": 656.3},
                {"name": "Franco-Italian Border", "curveCoordinates": [[43.3, 5.4], [44.3, 6.8], [45.8, 6.9]], "lengthKm": 488.0}
            ],
            "subRegions": [
                {"name": "Corsica", "status": "approved"}
            ],
            "protocol": "TCP/IP Secure"
        },
        {
            "name": "Germany",
            "isHistorical": True,
            "graphicShape": [[54.8, 8.4], [47.2, 10.4], [51.0, 14.8]],
            "borders": [
                {"name": "German-French Border", "curveCoordinates": [[47.6, 7.5], [49.2, 7.0], [49.2, 8.0]], "lengthKm": 451.0}
            ],
            "subRegions": [
                {"name": "Bavaria", "status": "approved"}
            ],
            "protocol": "HTTPS Diplomatic"
        },
        {
            "name": "Spain",
            "isHistorical": True,
            "graphicShape": [[43.3, -1.7], [36.0, -5.3], [37.0, -1.9], [42.3, 3.2]],
            "borders": [
                {"name": "Spanish-Portuguese Border", "curveCoordinates": [[42.1, -8.1], [38.2, -7.1], [37.2, -7.4]], "lengthKm": 1214.0}
            ],
            "subRegions": [
                {"name": "Catalonia", "status": "pending"},
                {"name": "Basque Country", "status": "pending"}
            ],
            "protocol": "TCP/IP Encrypted"
        },
        {
            "name": "Italy",
            "isHistorical": True,
            "graphicShape": [[45.8, 6.9], [46.5, 11.5], [40.8, 17.5], [38.1, 13.3]],
            "borders": [],
            "subRegions": [
                {"name": "Sicily", "status": "approved"},
                {"name": "Sardinia", "status": "approved"}
            ],
            "protocol": "WebSockets Secure"
        },
        {
            "name": "Portugal", "isHistorical": True,
            "graphicShape": [[42.1, -8.1], [37.0, -9.0], [37.2, -7.4]], "borders": [], "subRegions": [], "protocol": "HTTPS"
        },
        {
            "name": "Poland", "isHistorical": True,
            "graphicShape": [[54.8, 18.0], [49.2, 19.9], [51.0, 24.0], [54.3, 22.7]], "borders": [], "subRegions": [], "protocol": "TCP/IP"
        },
        {
            "name": "Romania", "isHistorical": True,
            "graphicShape": [[48.2, 26.6], [43.6, 25.3], [44.3, 28.6], [47.0, 28.0]], "borders": [], "subRegions": [{"name": "Transylvania", "status": "approved"}], "protocol": "Secure Sockets"
        },
        {
            "name": "Greece", "isHistorical": True,
            "graphicShape": [[41.7, 26.2], [36.3, 22.5], [35.0, 25.0], [40.8, 20.0]], "borders": [], "subRegions": [], "protocol": "HTTPS"
        },
        {
            "name": "Sweden", "isHistorical": True,
            "graphicShape": [[69.0, 20.5], [55.3, 13.0], [59.3, 18.0], [65.8, 24.1]], "borders": [], "subRegions": [], "protocol": "TCP/IP"
        },
        {
            "name": "Norway", "isHistorical": True,
            "graphicShape": [[71.1, 27.6], [57.9, 7.0], [62.0, 5.0], [69.0, 20.5]], "borders": [], "subRegions": [], "protocol": "TCP/IP"
        },
        {
            "name": "Finland", "isHistorical": True,
            "graphicShape": [[70.0, 28.0], [60.0, 22.0], [60.5, 27.5], [69.0, 29.0]], "borders": [], "subRegions": [], "protocol": "HTTPS"
        },
        {
            "name": "Austria", "isHistorical": True,
            "graphicShape": [[49.0, 15.0], [46.3, 14.0], [47.2, 9.5], [48.3, 16.9]], "borders": [], "subRegions": [], "protocol": "TCP/IP"
        },
        {
            "name": "Switzerland", "isHistorical": True,
            "graphicShape": [[47.8, 8.5], [45.8, 7.0], [46.2, 10.4]], "borders": [], "subRegions": [], "protocol": "HTTPS"
        },
        {
            "name": "Belgium", "isHistorical": True,
            "graphicShape": [[51.5, 4.5], [49.5, 5.5], [51.0, 2.5]], "borders": [], "subRegions": [], "protocol": "HTTPS"
        }
    ]
    database.countries.insert_many(countries)
    
    users = [
        {"username": "admin", "password": "admin123", "role": "PeaceCouncilMember", "fullName": "Admin Council"},
        {"username": "franta", "password": "franta123", "role": "HeadOfState", "fullName": "President of France", "contactDetails": "pres_fr@gov.eu", "country": "France"},
        {"username": "germania", "password": "germania123", "role": "HeadOfState", "fullName": "Chancellor of Germany", "contactDetails": "chan_de@gov.eu", "country": "Germany"},
        {"username": "spania", "password": "spania123", "role": "HeadOfState", "fullName": "Prime Minister of Spain", "contactDetails": "pm_es@gov.eu", "country": "Spain"},
        {"username": "italia", "password": "italia123", "role": "HeadOfState", "fullName": "President of Italy", "contactDetails": "pres_it@gov.eu", "country": "Italy"},
        {"username": "romania", "password": "romania123", "role": "HeadOfState", "fullName": "President of Romania", "contactDetails": "pres_ro@gov.eu", "country": "Romania"},
        {"username": "john", "password": "john123", "role": "Citizen", "fullName": "John Doe (Citizen)"},
        {"username": "maria", "password": "maria123", "role": "Citizen", "fullName": "Maria Rossi (Citizen)"}
    ]
    database.users.insert_many(users)
    
    requests = [
        {"requestName": "Corsican Independence", "issuingGroup": "Corsica Free", "category": "ethnic", "status": "pending", "country": "France"},
        {"requestName": "Bavarian Sovereignty", "issuingGroup": "Bavarian Party", "category": "state-supported", "status": "pending", "country": "Germany"}
    ]
    database.independence_requests.insert_many(requests)

    past_audiences = [
        {"requester": "president_fr", "protocol": "TCP/IP Secure", "contact": "pres_fr@gov.eu", "scheduledDate": "2026-05-10", "scheduledTime": "14:00:00", "chatType": "1:1", "timestamp": 1778410000000}
    ]
    database.audiences.insert_many(past_audiences)

    past_reports = [
        {"content": "Meeting concluded successfully. France and Germany reached a bilateral agreement regarding the border surveillance protocols. No further action needed.", "isPublic": True, "room": "past_room_1", "date": "2026-05-10 14:45:00"},
        {"content": "Classified discussion regarding the Basque Country requests. Highly confidential data was shared.", "isPublic": False, "room": "past_room_2", "date": "2026-05-11 09:30:00"}
    ]
    database.reports.insert_many(past_reports)

    print("Database seeded.")


@app.route('/')
def index():
    # Force DB connection
    connect_to_db()
    return render_template('index.html')

# API Endpoints
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    db = connect_to_db()
    user = db.users.find_one({"username": data.get('username')})
    if user and user.get('password') == data.get('password'):
        user['_id'] = str(user['_id'])
        return jsonify({"success": True, "user": user})
    return jsonify({"success": False, "message": "Invalid username or password"}), 401

@app.route('/api/countries', methods=['GET'])
def get_countries():
    db = connect_to_db()
    countries = list(db.countries.find({}))
    for c in countries:
        c['_id'] = str(c['_id'])
    return jsonify(countries)

@app.route('/api/requests', methods=['GET'])
def get_requests():
    db = connect_to_db()
    reqs = list(db.independence_requests.find({}))
    for r in reqs:
        r['_id'] = str(r['_id'])
    return jsonify(reqs)

@app.route('/api/requests/<req_id>', methods=['PUT'])
def update_request(req_id):
    data = request.json
    db = connect_to_db()
    from bson.objectid import ObjectId
    try:
        db.independence_requests.update_one({"_id": ObjectId(req_id)}, {"$set": {"status": data.get("status")}})
    except:
        # Handle mongomock str ids or valid objectids
        db.independence_requests.update_one({"_id": req_id}, {"$set": {"status": data.get("status")}})
    return jsonify({"success": True})

@app.route('/api/audiences/request', methods=['POST'])
def request_audience():
    data = request.json
    db = connect_to_db()
    
    # Simple scheduling logic: Schedule for 1 minute from now
    import datetime
    scheduled_time = datetime.datetime.now() + datetime.timedelta(minutes=1)
    
    audience = {
        "requester": data.get("username"),
        "protocol": data.get("protocol"),
        "contact": data.get("contact"),
        "scheduledDate": scheduled_time.strftime("%Y-%m-%d"),
        "scheduledTime": scheduled_time.strftime("%H:%M:%S"),
        "chatType": "1:1",
        "timestamp": scheduled_time.timestamp() * 1000
    }
    
    res = db.audiences.insert_one(audience)
    audience['_id'] = str(res.inserted_id)
    
    return jsonify({"success": True, "audience": audience})

@app.route('/api/audiences', methods=['GET'])
def get_audiences():
    db = connect_to_db()
    auds = list(db.audiences.find({}))
    for a in auds:
        a['_id'] = str(a['_id'])
    return jsonify(auds)

@app.route('/api/reports', methods=['GET'])
def get_reports():
    db = connect_to_db()
    reps = list(db.reports.find({}))
    for r in reps:
        r['_id'] = str(r['_id'])
    return jsonify(reps)

# WebSockets for Chat
@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('message', {'user': 'System', 'text': f'{username} has joined the audience room.'}, to=room)

@socketio.on('message')
def on_message(data):
    room = data['room']
    emit('message', {'user': data['username'], 'text': data['text']}, to=room)

@socketio.on('generate_report')
def on_generate_report(data):
    db = connect_to_db()
    report = {
        "content": data['content'],
        "isPublic": data['isPublic'],
        "room": data['room'],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    res = db.reports.insert_one(report)
    emit('report_generated', {"success": True}, to=data['room'])

if __name__ == '__main__':
    print("Starting Europa Peace server...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)

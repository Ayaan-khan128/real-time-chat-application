
import os
from datetime import datetime, timezone
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token,jwt_required,decode_token
from flask import request
from werkzeug.security import generate_password_hash
from flask_jwt_extended import JWTManager
from datetime import timedelta
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit,disconnect
from pymongo import MongoClient
from dotenv import load_dotenv
from pymongo.errors import DuplicateKeyError

load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("JWT_SECRET_KEY is missing. Check your .env file.")

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

jwt = JWTManager(app)

CORS(app, origins=["http://localhost:5173"])

socketio = SocketIO(
    app,
    cors_allowed_origins=["http://localhost:5173"]
)

# Connect to the local MongoDB database
mongo_uri = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017/"
)

mongo_client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=5000
)

db = mongo_client["chatspace_db"]
messages_collection = db["messages"]
users_collection = db["users"]
users_collection.create_index("username", unique=True)
users_collection.create_index("email", unique=True)
connected_users = {}
pending_message_senders = {}
message_senders = {}

@app.route("/")
def home():
    return jsonify({
        "message": "Real-Time Chat API is running!"
    })


@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "Real-Time Chat Backend"
    })


@app.route("/api/db-health")
def db_health():
    try:
          mongo_client.admin.command("ping")
          return jsonify({
          "status": "healthy",
           "database": "chatspace_db"
        })
    except Exception:
            app.logger.exception("MongoDB connection failed")
            return jsonify({
                "status": "unhealthy",
                "message": "Could not connect to MongoDB"
            }), 503
    

@app.route("/api/messages", methods=["GET"])

@jwt_required()

def get_messages():
    try:
        saved_messages = list(
            messages_collection.find(
                {},
                {"_id": 1, "message": 1, "sender": 1,"timestamp": 1}
            ).sort("_id", -1).limit(50)
        )

        saved_messages.reverse()

        for item in saved_messages:
            item["id"] = str(item.pop("_id"))

            if item.get("timestamp"):
               item["timestamp"] = item["timestamp"].isoformat()

        return jsonify({"messages": saved_messages})

    except Exception:
        app.logger.exception("Failed to load message history")
        return jsonify({
            "error": "Could not load messages"
        }), 500

    
@socketio.on("connect")
def handle_connect(auth):
    token = (auth or {}).get("token")

    if not token:
        return False

    try:
        decoded_token = decode_token(token)
        user_id = decoded_token.get("sub")

        if not user_id:
            return False

        user = users_collection.find_one(
            {"_id": __import__("bson").ObjectId(user_id)},
            {"username": 1}
        )

        if not user:
            return False

        connected_users[request.sid] = {
            "user_id": user_id,
            "username": user["username"]
        }

        # Notify all connected clients about online users
        online_users = list({
            user_data["username"]
            for user_data in connected_users.values()
        })

        socketio.emit("online_users", online_users)

    except Exception:
        return False

@socketio.on("disconnect")
def handle_disconnect():
    connected_users.pop(request.sid, None)

    # Notify all connected clients about updated online users
    online_users = list({
        user_data["username"]
        for user_data in connected_users.values()
    })

    socketio.emit("online_users", online_users)  

@socketio.on("typing")
def handle_typing(data):
    current_user = connected_users.get(request.sid)

    if not current_user:
        return

    is_typing = (data or {}).get("is_typing", False)

    socketio.emit(
        "user_typing",
        {
            "username": current_user["username"],
            "is_typing": bool(is_typing)
        },
        skip_sid=request.sid
    )    

@socketio.on("send_message")
def handle_message(data):
    current_user = connected_users.get(request.sid)

    # Reject messages from unauthenticated connections
    if not current_user:
        disconnect()
        return

    if not isinstance(data, dict):
     return {"status": "error", "message": "Invalid message data"}

    message = data.get("message", "")

    if not isinstance(message, str):
      return {"status": "error", "message": "Message must be text"}

    message = message.strip()

    if not message:
      return {"status": "error", "message": "Message cannot be empty"}

    if len(message) > 2000:
     return {"status": "error", "message": "Message is too long"}

    # Use the authenticated username, not the client's supplied sender
    sender = current_user["username"]

    saved_message = {
    "message": message,
    "sender": sender,
    "timestamp": datetime.now(timezone.utc)
}

    try:
        result = messages_collection.insert_one(saved_message)
        pending_message_senders[str(result.inserted_id)] = request.sid
        message_senders[str(result.inserted_id)] = {
    "sender_sid": request.sid,
    "sender_user_id": current_user["user_id"]
}
        emit(
            "receive_message",
            {
                "id": str(result.inserted_id),
                "message": message,
                "sender": sender,
                "timestamp": saved_message["timestamp"].isoformat()
            },
            broadcast=True
        )

        # Confirm successful database storage to the sender
        return {
            "status": "sent",
            "id": str(result.inserted_id)
        }

    except Exception:
        app.logger.exception("Failed to save chat message")
        return {"status": "error"}



@socketio.on("message_delivered")
def handle_message_delivered(data):
    current_user = connected_users.get(request.sid)

    if not current_user or not isinstance(data, dict):
        return

    message_id = data.get("id")

    if not message_id:
        return

    sender_sid = pending_message_senders.get(message_id)

    if not sender_sid or sender_sid == request.sid:
        return

    socketio.emit(
        "message_status",
        {
            "id": message_id,
            "status": "delivered"
        },
        to=sender_sid
    )

    pending_message_senders.pop(message_id, None)   


@socketio.on("message_read")
def handle_message_read(data):
    current_user = connected_users.get(request.sid)

    if not current_user or not isinstance(data, dict):
        return

    message_id = data.get("id")

    if not message_id:
        return

    message_info = message_senders.get(message_id)

    if not message_info:
        return

    # Only another authenticated user can mark it as read
    if current_user["user_id"] == message_info["sender_user_id"]:
        return

    socketio.emit(
        "message_status",
        {
            "id": message_id,
            "status": "read"
        },
        to=message_info["sender_sid"]
    )

    message_senders.pop(message_id, None)     
 
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "")
    email = data.get("email", "")
    password = data.get("password", "")

    if not isinstance(username, str) or not isinstance(email, str) or not isinstance(password, str):
     return jsonify({
        "error": "Username, email, and password must be text"
    }), 400

    username = username.strip()
    email = email.strip().lower()

    if not username or not email or not password:
        return jsonify({
            "error": "Username, email, and password are required"
        }), 400

    if len(password) < 8:
        return jsonify({
            "error": "Password must be at least 8 characters"
        }), 400

    existing_user = users_collection.find_one({
        "$or": [
            {"username": username},
            {"email": email}
        ]
    })

    if existing_user:
        return jsonify({
            "error": "Username or email is already registered"
        }), 409

    user = {
        "username": username,
        "email": email,
        "password_hash": generate_password_hash(password)
    }

    try:
        users_collection.insert_one(user)

    except DuplicateKeyError:
        return jsonify({
            "error": "Username or email is already registered"
        }), 409

    except Exception:
        app.logger.exception("Registration failed")
        return jsonify({
            "error": "Registration failed. Please try again."
        }), 500

    return jsonify({
        "message": "Registration successful"
    }), 201

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "")
    password = data.get("password", "")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({
            "error": "Email and password must be text"
        }), 400

    email = email.strip().lower()

    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    try:
        user = users_collection.find_one({"email": email})

        if not user or not check_password_hash(
            user["password_hash"], password
        ):
            return jsonify({
                "error": "Invalid email or password"
            }), 401

        access_token = create_access_token(
            identity=str(user["_id"])
        )

        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "username": user["username"]
        }), 200

    except Exception:
        app.logger.exception("Login failed")
        return jsonify({
            "error": "Login failed. Please try again."
        }), 500

if __name__ == "__main__":
    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=True
    )



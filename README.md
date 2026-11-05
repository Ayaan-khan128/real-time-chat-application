# Real-Time Chat Application

A full-stack real-time chat application built using **React, Flask, MongoDB, and Socket.IO**. It enables authenticated users to communicate instantly through a shared chat room.

## Features

- User registration and login
- JWT-based authentication
- Secure password hashing
- Real-time messaging using Socket.IO
- MongoDB message persistence
- Online users tracking
- Live typing indicators
- Message timestamps
- Sent, delivered, and read indicators
- Input validation and duplicate account protection
- Protected message history API

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React.js, Vite |
| Backend | Python, Flask |
| Database | MongoDB |
| Real-time communication | Flask-SocketIO |
| API | REST API |
| Authentication | JWT |
| Password security | Werkzeug password hashing |
| Frontend communication | Fetch API, Socket.IO Client |

## Project Structure

```text
Real-time-chat-app/
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── .env
│   └── .gitignore
│
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Login.jsx
    │   │   └── Register.jsx
    │   ├── App.jsx
    │   └── App.css
    ├── package.json
    └── index.html
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd Real-time-chat-app
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
```

Activate the virtual environment on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file inside the backend folder:

```env
MONGO_URI=mongodb://localhost:27017/
JWT_SECRET_KEY=your_secure_random_secret
```

Start the Flask backend:

```bash
python app.py
```

Backend runs at:

`http://127.0.0.1:5000/`

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

`http://localhost:5173/`

### 4. Database Setup

Install and start MongoDB locally.

The application uses:

- Database: `chatspace_db`
- Users collection: `users`
- Messages collection: `messages`

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Backend status |
| GET | `/api/health` | API health check |
| GET | `/api/db-health` | Database health check |
| POST | `/api/register` | Register a user |
| POST | `/api/login` | Authenticate a user |
| GET | `/api/messages` | Retrieve chat history (JWT protected) |

## Socket.IO Events

| Event | Purpose |
|---|---|
| `connect` | Authenticate a socket connection |
| `disconnect` | Handle user disconnection |
| `send_message` | Send a chat message |
| `receive_message` | Receive a broadcast message |
| `online_users` | Update online users |
| `typing` | Notify other users about typing |
| `user_typing` | Display typing indicator |
| `message_delivered` | Acknowledge message delivery |
| `message_read` | Acknowledge message reading |
| `message_status` | Update message status |

## Security Features

- JWT authentication for protected resources
- Password hashing instead of plaintext password storage
- MongoDB unique indexes for usernames and emails
- Server-side message validation
- Authenticated sender identification
- Protected message history endpoint



## Future Improvements

- Private one-to-one conversations
- Persistent message delivery and read receipts
- Image and file sharing
- Message search and pagination
- Group chat management

## Author

Developed as part of the CODTECH IT Solutions internship program.

**Project:** Real-Time Chat Application

**Technologies:** Flask, React, MongoDB, Socket.IO and JWT.

---


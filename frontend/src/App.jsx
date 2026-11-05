
import { useEffect, useRef, useState } from "react";
import { io } from "socket.io-client";
import Login from "./pages/Login";
import Register from "./pages/Register";
import "./App.css";

function App() {
  const [username, setUsername] = useState(
    localStorage.getItem("username") || ""
  );

  const [authenticated, setAuthenticated] = useState(
    Boolean(localStorage.getItem("token"))
  );

  const [showRegister, setShowRegister] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [typingUser, setTypingUser] = useState("");

  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  function handleLogout() {
    socketRef.current?.disconnect();
    socketRef.current = null;

    localStorage.removeItem("token");
    localStorage.removeItem("username");

    setAuthenticated(false);
    setUsername("");
    setMessages([]);
    setMessage("");
    setConnected(false);
    setShowRegister(false);
  }

  useEffect(() => {
    if (!authenticated) return;

    const token = localStorage.getItem("token");

    if (!token) {
      handleLogout();
      return;
    }

    let cancelled = false;
    let socket = null;

    async function startChat() {
      try {
        const response = await fetch(
          "http://127.0.0.1:5000/api/messages",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (cancelled) return;

        if (response.status === 401) {
          handleLogout();
          return;
        }

        if (!response.ok) {
          throw new Error("Unable to load messages.");
        }

        const data = await response.json();

        if (cancelled) return;

        setMessages(
          data.messages.map((item) => ({
            id: item.id,
            text: item.message,
            sender: item.sender,
            timestamp: item.timestamp || null,
          }))
        );

        socket = io("http://127.0.0.1:5000", {
          auth: { token },
        });

        socketRef.current = socket;

        socket.on("connect", () => {
          setConnected(true);
        });

        socket.on("disconnect", () => {
          setConnected(false);
        });

        socket.on("online_users", (users) => {
  setOnlineUsers(users);
});

socket.on("user_typing", (data) => {
  if (data.is_typing) {
    setTypingUser(data.username);
  } else {
    setTypingUser("");
  }
});

        socket.on("connect_error", (error) => {
          console.error("Socket connection error:", error.message);

          if (
            /token|unauthorized|authentication/i.test(error.message)
          ) {
            handleLogout();
          }
        });

        socket.on("receive_message", (data) => {
  setMessages((previous) => [
    ...previous,
    {
      id: data.id || `${Date.now()}-${Math.random()}`,
      text: data.message,
      sender: data.sender,
      timestamp: data.timestamp || null,
      status: data.sender === username ? "sent" : null,
    },
  ]);

  // Acknowledge delivery only for another user's message
  if (data.sender !== username && data.id) {
    socket.emit("message_delivered", {
      id: data.id,
    });
  }
  if (data.sender !== username && data.id) {
  socket.emit("message_read", {
    id: data.id,
  });
}
});
socket.on("message_status", (data) => {
  setMessages((previous) =>
    previous.map((item) =>
      item.id === data.id
        ? { ...item, status: data.status }
        : item
    )
  );
});
      } catch (error) {
        if (!cancelled) {
          console.error("Chat startup error:", error);
        }
      }
    }

    startChat();

    return () => {
      cancelled = true;
      socket?.disconnect();

      if (socketRef.current === socket) {
        socketRef.current = null;
      }
    };
  }, [authenticated]);

  useEffect(() => {
  messagesEndRef.current?.scrollIntoView({
    behavior: "smooth",
  });
}, [messages]);

  function handleLogin(loggedInUsername) {
    setUsername(loggedInUsername);
    setMessages([]);
    setAuthenticated(true);
  }

  function handleMessageChange(value) {
  setMessage(value);

  if (!socketRef.current?.connected) return;

  if (typingTimeoutRef.current) {
    clearTimeout(typingTimeoutRef.current);
  }

  if (value.trim()) {
    socketRef.current.emit("typing", {
      is_typing: true,
    });

    typingTimeoutRef.current = setTimeout(() => {
      socketRef.current?.emit("typing", {
        is_typing: false,
      });
    }, 1000);
  } else {
    socketRef.current.emit("typing", {
      is_typing: false,
    });
  }
}

  function sendMessage(e) {
  e.preventDefault();

  const text = message.trim();

  if (!text || !socketRef.current?.connected) return;

  socketRef.current.emit(
    "send_message",
    { message: text },
    (response) => {
     if (response?.status === "sent") {
  setMessages((previous) =>
    previous.map((item) =>
      item.id === response.id
        ? { ...item, status: "sent" }
        : item
    )
  );
} else {
  console.error("Message could not be saved.");
}
    }
  );

  setMessage("");
}
  if (!authenticated) {
    return showRegister ? (
      <Register onShowLogin={() => setShowRegister(false)} />
    ) : (
      <Login
        onLogin={handleLogin}
        onShowRegister={() => setShowRegister(true)}
      />
    );
  }

  return (
    <div className="chat-app">
      <aside className="sidebar">
        <h2>ChatSpace</h2>
        <p className="sidebar-label">MESSAGES</p>

        <div className="conversation active">
          <div className="avatar">
            {username.charAt(0).toUpperCase()}
          </div>

          <div>
            <strong>Chat Room</strong>
            <p>{connected ? "Connected" : "Connecting..."}</p>
          </div>
        </div>
        <div className="online-users-section">
  <p className="sidebar-label">ONLINE USERS</p>

  {onlineUsers.length > 0 ? (
    onlineUsers.map((user) => (
      <div className="online-user" key={user}>
        <span className="online-dot"></span>
        <span>{user}</span>
      </div>
    ))
  ) : (
    <p className="no-online-users">No users online</p>
  )}
</div>
      </aside>

      <main className="chat-main">
        <header className="chat-header">
          <div className="avatar">
            {username.charAt(0).toUpperCase()}
          </div>

          <div>
            <h3>Chat Room</h3>
            <p>
              {connected ? "Online" : "Connecting to server..."}
            </p>
          </div>

          <button type="button" onClick={handleLogout}>
            Log Out
          </button>
        </header>

        <section className="messages">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">✉</div>
              <h3>Welcome to ChatSpace!</h3>
              <p>Send a message to start chatting.</p>
            </div>
          ) : (
            messages.map((item) => (
             <div
  className={`message-row ${
    item.sender === username ? "own-message" : "other-message"
  }`}
  key={item.id}
>
                <div className="message-bubble">
                  <small>{item.sender}</small>
<p>{item.text}</p>
{item.sender === username && item.status && (
  <span
    className={`message-status ${
      item.status === "read" ? "read-status" : ""
    }`}
  >
    {item.status === "read"
      ? "✓✓ Read"
      : item.status === "delivered"
      ? "✓✓ Delivered"
      : "✓ Sent"}
  </span>
)}

{item.timestamp && (
  <time className="message-time">
    {new Date(item.timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    })}
  </time>
)}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </section>

        {typingUser && (
  <div className="typing-indicator">
    {typingUser} is typing...
  </div>
)}

        <form className="message-form" onSubmit={sendMessage}>
          <input
            type="text"
            placeholder="Type your message..."
            value={message}
            onChange={(e) => handleMessageChange(e.target.value)}
            disabled={!connected}
          />

          <button type="submit" disabled={!connected}>
            Send ➤
          </button>
        </form>
      </main>
    </div>
  );
}

export default App;


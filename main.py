from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# HTML for the client
html = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WebSocket Chat Room</title>
        <style>
            body {
                margin: 0;
                padding: 0;
                font-family: 'Arial', sans-serif;
                background-color: #f4f4f4;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }

            .chat-container {
                width: 100%;
                max-width: 600px;
                background-color: white;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                border-radius: 10px;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                height: 80vh;
            }

            .chat-header {
                background-color: #007bff;
                padding: 15px;
                color: white;
                text-align: center;
                font-size: 24px;
            }

            .chat-messages {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                background-color: #f0f0f0;
            }

            .chat-messages ul {
                list-style: none;
                padding: 0;
            }

            .chat-messages ul li {
                padding: 10px;
                margin-bottom: 10px;
                background-color: #007bff;
                color: white;
                border-radius: 5px;
                max-width: 80%;
                word-wrap: break-word;
            }

            .chat-footer {
                display: flex;
                padding: 10px;
                background-color: #007bff;
            }

            .chat-footer input {
                flex: 1;
                padding: 10px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
                margin-right: 10px;
            }

            .chat-footer button {
                padding: 10px 15px;
                font-size: 16px;
                background-color: white;
                color: #007bff;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                transition: background-color 0.3s;
            }

            .chat-footer button:hover {
                background-color: #0056b3;
                color: white;
            }

            @media (max-width: 768px) {
                .chat-container {
                    width: 90%;
                    height: 85vh;
                }

                .chat-header {
                    font-size: 20px;
                }

                .chat-footer input,
                .chat-footer button {
                    font-size: 14px;
                }
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">
                WebSocket Chat Room
            </div>
            <div class="chat-messages">
                <ul id="messages">
                </ul>
            </div>
            <div class="chat-footer">
                <input type="text" id="messageText" placeholder="Type your message..." autocomplete="off" disabled>
                <button onclick="sendMessage()" disabled>Send</button>
            </div>
        </div>

        <script>
            let username = null;
            const ws = new WebSocket("wss://websockets-for-real-time-communication-1.onrender.com/ws");

            // Ask for user's name when the page loads
            window.onload = function() {
                username = prompt("Enter your name:");
                if (username && username.trim() !== "") {
                    document.getElementById("messageText").disabled = false;
                    document.querySelector("button").disabled = false;
                } else {
                    username = "Anonymous";
                }
            }

            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');
                var message = document.createElement('li');
                message.textContent = event.data;
                messages.appendChild(message);

                // Auto-scroll to the bottom when a new message is added
                messages.scrollTop = messages.scrollHeight;
            };

            function sendMessage() {
                var input = document.getElementById("messageText");
                if (input.value.trim() !== "") {
                    const messageData = {
                        name: username,
                        message: input.value
                    };
                    ws.send(JSON.stringify(messageData));
                    input.value = '';
                }
            }

            // Handle enter key press for sending messages
            document.getElementById("messageText").addEventListener("keypress", function(event) {
                if (event.key === "Enter") {
                    event.preventDefault();
                    sendMessage();
                }
            });
        </script>
    </body>
</html>
"""

# WebSocket Manager to handle multiple connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

# Instantiate the WebSocket manager
manager = ConnectionManager()

# Serve the HTML file at the root URL
@app.get("/", response_class=HTMLResponse)
async def get():
    return html

# WebSocket connection route
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Parse the incoming message (name and message)
            message_data = eval(data)  # Use eval for simplicity, but prefer JSON parsing in real apps
            message = f"{message_data['name']} says: {message_data['message']}"
            await manager.broadcast(message)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("A client has disconnected.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

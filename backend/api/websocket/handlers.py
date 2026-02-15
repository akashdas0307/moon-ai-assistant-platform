"""WebSocket message handlers."""
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import logging
import uuid
from .connection import manager

logger = logging.getLogger(__name__)


async def handle_websocket(websocket: WebSocket):
    """
    Main WebSocket handler - accepts connections and processes messages.

    Args:
        websocket: The WebSocket connection
    """
    # Generate unique client ID
    client_id = str(uuid.uuid4())

    try:
        # Accept the connection
        await manager.connect(websocket, client_id)

        # Send welcome message
        await manager.send_message(client_id, {
            "type": "connection",
            "status": "connected",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to Moon-AI WebSocket server"
        })

        # Listen for messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                logger.info(f"Received from {client_id}: {message}")

                # Echo the message back with metadata
                response = {
                    "type": "echo",
                    "original_message": message,
                    "client_id": client_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "server_message": f"Server received: {message.get('content', 'No content')}"
                }

                await manager.send_message(client_id, response)

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {data}")
                await manager.send_message(client_id, {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected normally")
        manager.disconnect(client_id)

    except Exception as e:
        logger.error(f"Error in WebSocket handler for {client_id}: {e}")
        manager.disconnect(client_id)

"""WebSocket message handlers."""
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import logging
import uuid
from .connection import manager
from backend.core.agent import head_agent
from backend.core.communication.service import save_message
from backend.models.communication import CommunicationCreate

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
                message_data = json.loads(data)
                logger.info(f"Received from {client_id}: {message_data}")

                content = message_data.get('content', '')
                last_com_id = message_data.get('last_com_id')

                if not content:
                    continue

                # --- 1. Save User Message ---
                user_com_id = None
                try:
                    user_comm = save_message(CommunicationCreate(
                        sender="user",
                        recipient="assistant",
                        raw_content=content,
                        initiator_com_id=last_com_id
                    ))
                    user_com_id = str(user_comm.com_id)
                except Exception as e:
                    logger.error(f"Failed to save user message: {e}")
                    # Continue without saving, chat should not break

                if head_agent:
                    # Streaming logic
                    message_id = str(uuid.uuid4())

                    # --- 2. Send stream start with user_com_id ---
                    await manager.send_message(client_id, {
                        "type": "stream_start",
                        "message_id": message_id,
                        "user_com_id": user_com_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                    accumulated = ""
                    try:
                        # Process message through agent (streaming)
                        async for token in head_agent.process_message(content):
                            # Send token
                            await manager.send_message(client_id, {
                                "type": "stream_token",
                                "message_id": message_id,
                                "token": token,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                            accumulated += token
                    except Exception as e:
                        logger.error(f"Error during streaming for {client_id}: {e}")

                    # --- 3. Save AI Message ---
                    ai_com_id = None
                    if accumulated:
                        try:
                            ai_comm = save_message(CommunicationCreate(
                                sender="assistant",
                                recipient="user",
                                raw_content=accumulated,
                                initiator_com_id=user_com_id
                            ))
                            ai_com_id = str(ai_comm.com_id)
                        except Exception as e:
                            logger.error(f"Failed to save AI message: {e}")

                    # --- 4. Send stream end with ai_com_id ---
                    await manager.send_message(client_id, {
                        "type": "stream_end",
                        "message_id": message_id,
                        "content": accumulated,
                        "sender": "assistant",
                        "ai_com_id": ai_com_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                else:
                    # Fallback if agent failed to initialize
                    response_text = f"Agent not configured. Echo: {content}"
                    logger.warning("HeadAgent not available, using fallback echo.")

                    # Build response (legacy format)
                    response = {
                        "type": "message",
                        "content": response_text,
                        "sender": "assistant",
                        "client_id": client_id,
                        "timestamp": datetime.utcnow().isoformat(),
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

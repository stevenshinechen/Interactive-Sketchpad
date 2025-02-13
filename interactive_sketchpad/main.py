import tempfile

import chainlit as cl
from chainlit.context import init_ws_context
from chainlit.session import WebsocketSession
from chainlit.utils import mount_chainlit
from fastapi import FastAPI, File, Request, UploadFile

from interactive_sketchpad.chatbot import main

app = FastAPI()

# Handle uploaded images
@app.post("/upload")
async def upload_image(
    session_id: str,
    text: str = "Here's my working so far, can you help me?",
    file: UploadFile = File(...),
):
    ws_session = WebsocketSession.get_by_id(session_id=session_id)
    init_ws_context(ws_session)

    content = await file.read()

    image_element = cl.Image(
        name=file.filename, content=content, display="inline", size="large"
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as temp_file:
        temp_file.write(content)
        temp_file_path = temp_file.name  # Get the temporary file path
        image_element.path = temp_file_path

        message = cl.Message(content=text, elements=[image_element])
        await message.send()
        await main(message)

    return {"message": "Image received"}


mount_chainlit(app=app, target="chatbot.py", path="/interactive_sketchpad")

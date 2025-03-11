import json
import os
import subprocess
from io import BytesIO
from pathlib import Path
import time
from typing import List

import chainlit as cl
import httpx
from chainlit.config import config
from chainlit.element import Element
from dotenv import load_dotenv
from literalai.helper import utc_now
from openai import AsyncAssistantEventHandler, AsyncOpenAI, OpenAI

from dynamic_sketchpad.tools import Tool
from interactive_sketchpad.prompt import GeoPrompt

load_dotenv()

async_openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
sync_openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

instructions = """
You are a tutor, your goal is to help the student solve a problem, giving short, subtle hints to help the student solve the problem.
You will be given a problem, question or working from the user and you should respond in a brief and concise way.
You should reuse the code from existing diagrams if drawing similar ones
You should only give one hint at a time, DO NOT give away the answer to the student.
You want to help the student visualize the problem so
you should give your response with text interleaved with helpful diagrams.
You MUST draw these diagrams by writing code using code interpreter.
First visualize using a diagram, then give the hint using the diagram.

Example:
[Image 1]
[Text 1]
[Image 2]
[Text 2]

You should only respond concisely, allowing the student to ask questions and respond
before continuing.
The aim is to get the student to reach to the answer independently, without
giving the answer away.
If you think a visualization is helpful, you can plot it without asking the
student's permission.

When drawing a series of diagrams, you should make the visualizations
intuitive and easy to understand.
For example, if you are showing a graph traversal as a series of diagrams,
you should highlight visited nodes, visited edges, nodes that you are about to visit etc.
in different colors.

Here is an example of how you should respond to the student:
<Student>
There are a total of numCourses courses you have to take, labeled from 0 to numCourses - 1. You are given an array prerequisites where prerequisites[i] = [ai, bi] indicates that you must take course bi first if you want to take course ai.

For example, the pair [0, 1], indicates that to take course 0 you have to first take course 1.
Return true if you can finish all courses. Otherwise, return false.
</Student>

<Tutor>
Let's try to make an example,
Input: numCourses = 2, prerequisites = [[1,0]]
Output: true

Let's draw a diagram to visualize this
[Draw diagram with Code Interpeter]

Explanation: There are a total of 2 courses to take. 
To take course 1 you should have finished course 0. So it is possible.
</Tutor>

<Student>
I'm still not sure how to get started.
</Student>

<Tutor>
This problem is equivalent to finding if a cycle exists in a directed graph.
If a cycle exists, no topological ordering exists and therefore it will be impossible to take all courses.

Let's draw a series of diagrams traversing through the graph and finding a cycle
[Draw a couple of diagrams showing traversal of the graph until cycle is found]
[Explanation of the diagrams]
</Tutor>

You should only give the solution if the student explicitly asks for it.
ALWAYS write math in $ dollar signs for latex rendering, for example $\sinx$
"""

assistant = sync_openai_client.beta.assistants.create(
    instructions=instructions,
    model="gpt-4o",
    tools=[Tool.CODE_INTERPRETER.to_dict()],
    name="Interactive Sketchpad",
    temperature=0,
)

config.ui.name = assistant.name

canvas_process = None


CANVAS_APP_URL = "http://0.0.0.0:8081/send_image_to_canvas"


async def send_image_to_canvas(image_bytes: bytes):
    """Sends the generated image (in bytes) to the drawing app for display asynchronously using httpx."""
    async with httpx.AsyncClient() as client:
        files = {"file": ("generated.png", BytesIO(image_bytes), "image/png")}
        response = await client.post(CANVAS_APP_URL, files=files)

        if response.status_code == 200:
            print("Image successfully sent to interactive canvas")
        else:
            print("Failed to send image:", response.text)


class EventHandler(AsyncAssistantEventHandler):

    def __init__(self, assistant_name: str) -> None:
        super().__init__()
        self.current_message: cl.Message = None
        self.current_step: cl.Step = None
        self.current_tool_call = None
        self.assistant_name = assistant_name

    async def on_text_created(self, text) -> None:
        self.current_message = await cl.Message(
            author=self.assistant_name, content=""
        ).send()

    async def on_text_delta(self, delta, snapshot):
        await self.current_message.stream_token(delta.value)

    async def on_text_done(self, text):
        await self.current_message.update()

    async def on_tool_call_created(self, tool_call):
        self.current_tool_call = tool_call.id
        self.current_step = cl.Step(name=tool_call.type, type="tool")
        self.current_step.language = "python"
        self.current_step.created_at = utc_now()
        await self.current_step.send()

    async def on_tool_call_delta(self, delta, snapshot):
        if snapshot.id != self.current_tool_call:
            self.current_tool_call = snapshot.id
            self.current_step = cl.Step(name=delta.type, type="tool")
            self.current_step.language = "python"
            self.current_step.start = utc_now()
            await self.current_step.send()

        if delta.type == "code_interpreter":
            if delta.code_interpreter.outputs:
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        error_step = cl.Step(name=delta.type, type="tool")
                        error_step.is_error = True
                        error_step.output = output.logs
                        error_step.language = "markdown"
                        error_step.start = self.current_step.start
                        error_step.end = utc_now()
                        await error_step.send()
            else:
                if delta.code_interpreter.input:
                    await self.current_step.stream_token(delta.code_interpreter.input)

    async def on_tool_call_done(self, tool_call):
        self.current_step.end = utc_now()
        await self.current_step.update()

    async def on_image_file_done(self, image_file, show_image: bool = False):
        image_id = image_file.file_id
        response = await async_openai_client.files.with_raw_response.content(image_id)

        if show_image:
            # Show image in chatbot interface
            image_element = cl.Image(
                name=image_id, content=response.content, display="inline", size="large"
            )
            if not self.current_message.elements:
                self.current_message.elements = []
            self.current_message.elements.append(image_element)
            await self.current_message.update()
        
        # Send image to whiteboard
        await send_image_to_canvas(response.content)


async def upload_files(files: List[Element], purpose: str = "assistants"):
    file_ids = []
    for file in files:
        uploaded_file = await async_openai_client.files.create(
            file=Path(file.path), purpose=purpose
        )
        file_ids.append(uploaded_file.id)
    return file_ids


async def process_files(files: List[Element]):
    # Upload files if any and get file_ids
    file_ids = []
    if len(files) > 0:
        file_ids = await upload_files(files)

    return [
        {
            "file_id": file_id,
            "tools": [{"type": "code_interpreter"}]
            + ([{"type": "file_search"}] if file.type in ["text", "pdf"] else []),
        }
        for file_id, file in zip(file_ids, files)
    ]


async def append_images_to_message(message: cl.Message) -> None:
    image_files = [file for file in message.elements if file.type == "image"]
    file_ids = await upload_files(image_files, purpose="vision")

    text_content = message.content
    message.content = []
    if text_content:
        message.content.append({"type": "text", "text": text_content})

    for file_id in file_ids:
        message.content.append(
            {"type": "image_file", "image_file": {"file_id": file_id}}
        )


@cl.on_chat_start
async def start_chat():
    thread = await async_openai_client.beta.threads.create()
    cl.user_session.set("thread_id", thread.id)
    print("Session id:", cl.user_session.get("id"))
    await cl.Message(
        content=f"Hello, I'm {assistant.name}! Your AI tutor that can draw! What can I help you with?"
    ).send()

    # Start the drawing app with session ID as a command-line argument
    global canvas_process
    canvas_process = subprocess.Popen(
        ["python", "interactive_canvas.py", cl.user_session.get("id")]
    )

    # Uncomment to run geometry3k
    # await prompt_geometry_3k_question(question_path="geometry/2079/ex.json")


@cl.on_chat_end
async def end_chat():
    """Terminate the drawing app when chat ends."""
    global canvas_process

    if canvas_process and canvas_process.poll() is None:  # Check if running
        canvas_process.terminate()
        canvas_process.wait()
        canvas_process = None
        print("Interactive canvas closed.")


@cl.on_message
async def main(message: cl.Message):
    thread_id = cl.user_session.get("thread_id")

    attachments = await process_files(message.elements)
    await append_images_to_message(message)

    visualize_message = {
        "type": "text",
        "text": "Visualize using Code Interpreter if you think it would be helpful, write math in $ dollar signs $",
    }
    oai_message = await async_openai_client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message.content + [visualize_message],
        attachments=attachments,
    )

    async with async_openai_client.beta.threads.runs.stream(
        thread_id=thread_id,
        assistant_id=assistant.id,
        event_handler=EventHandler(assistant_name=assistant.name),
    ) as stream:
        await stream.until_done()


async def prompt_geometry_3k_question(question_path: str):
    """Prompts with question from Geometry3k"""
    with open(question_path, "r") as file:
        question = json.load(file)
        prompt = GeoPrompt().initial_prompt(question, n_images=1)
        await cl.Message(content=f"Question:\n{question["annotat_text"]}").send()
        message = cl.Message(content=prompt)
        await main(message)

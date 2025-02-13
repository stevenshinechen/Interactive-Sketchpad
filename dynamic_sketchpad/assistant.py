import os
from io import BytesIO

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.beta import Thread
from openai.types.beta.threads import Message, Run
from PIL import Image, ImageFile
from tenacity import retry, stop_after_attempt, wait_random_exponential
from tqdm import tqdm

from dynamic_sketchpad.openai_utils import (
    display_message,
    get_image_bytes_from_message,
    get_strings_from_message,
    process_message,
)
from dynamic_sketchpad.tools import Tool

load_dotenv()


class Assistant:
    def __init__(self, instructions: str, tools: list[Tool], llm_str: str = "gpt-4o"):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        tool_dicts = [tool.to_dict() for tool in tools]
        self.assistant = self.client.beta.assistants.create(
            instructions=instructions, model=llm_str, tools=tool_dicts
        )

    def create_thread_and_run(self, user_input: str) -> tuple[Thread, Run]:
        print(f"Creating thread and run for {user_input=}, {type(user_input)=}")
        thread = self.client.beta.threads.create()
        run = self.submit_message(user_input, thread.id)
        return thread, run

    def submit_message(self, user_message: str, thread_id: str) -> Run:
        self.client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=user_message
        )
        return self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant.id,
        )

    def gather_runs(self, *runs: Run) -> list[Run]:
        runs = [self.poll_run(run) for run in tqdm(runs, desc="Polling runs")]
        for run in runs:
            if run.status != "completed":
                print(f"WARNING: Run {run.id} is not complete. {run=}")
        return runs

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    def poll_run(self, run: Run) -> Run:
        return self.client.beta.threads.runs.poll(run.id, run.thread_id)

    def last_messages(
        self, thread_id: str, include_user: bool = False
    ) -> list[Message]:
        messages = self.client.beta.threads.messages.list(thread_id)

        responses = []
        for message in messages.data:
            if message.role == "assistant":
                responses.append(message)
            else:
                if include_user:
                    responses.append(message)
                break

        return responses

    def invoke_all(self, *prompts: str) -> list[list[Message]]:
        threads_and_runs = [self.create_thread_and_run(prompt) for prompt in prompts]
        runs = self.gather_runs(*[run for _, run in threads_and_runs])
        messages = [self.last_messages(run.thread_id) for run in runs]
        return messages

    def invoke(self, prompt: str) -> list[Message]:
        thread, run = self.create_thread_and_run(prompt)
        run = self.poll_run(run)
        messages = self.last_messages(run.thread_id)
        return messages

    def prompt(self, prompt: str) -> list[str | bytes]:
        messages = self.invoke(prompt)
        processed_messages = []
        for message in messages:
            processed_messages.extend(process_message(self.client, message))

        return processed_messages

    def messages_to_string(self, messages: list[Message]) -> str:
        text_messages = []
        for message in messages:
            text_messages.extend(self.get_strings_from_message(message))

        # The messages are ordered from newest to oldest, so we reverse them
        text_messages = reversed(text_messages)
        return "\n".join(text_messages)

    def messages_to_images(self, messages: list[Message]) -> list[ImageFile.ImageFile]:
        images = []
        for message in messages:
            images.extend(self.message_to_images(message))

        # The images are ordered from newest to oldest, so we reverse them
        images = reversed(images)
        return images

    def message_to_images(self, message: Message) -> list[ImageFile.ImageFile]:
        all_image_bytes = self.get_image_bytes_from_message(message)
        images = []
        for image_bytes in all_image_bytes:
            images.append(Image.open(BytesIO(image_bytes)))

        return images

    def get_strings_from_message(self, message: Message) -> list[str]:
        return get_strings_from_message(message)

    def get_image_bytes_from_message(self, message: Message) -> list[bytes]:
        return get_image_bytes_from_message(self.client, message)

    def display_message(self, message: Message, interactive: bool = False) -> None:
        return display_message(self.client, message, interactive=interactive)

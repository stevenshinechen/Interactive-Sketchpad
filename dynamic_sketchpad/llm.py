import asyncio
import os
from typing import Dict, TypedDict, TypeVar

from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types import Completion
from openai.types.chat.parsed_chat_completion import ParsedChatCompletion
from tenacity import retry, stop_after_attempt, wait_random_exponential
from tqdm.asyncio import tqdm

load_dotenv()

ResponseFormatT = TypeVar("ResponseFormatT")


class Message(TypedDict):
    role: str
    content: str


def create_message(role: str, content: str) -> Message:
    return {"role": role, "content": content}


def from_messages_to_prompt(
    messages: list[Message], role_map: Dict[str, str], assistant_role: str
) -> str:
    return (
        "\n".join(
            [
                f"{role_map.get(msg['role'], msg['role'])}: {msg['content']}"
                for msg in messages
            ]
        )
        + f"\n{assistant_role}:"
    )


class LLM:
    def __init__(
        self, llm_str: str = "gpt-4o", default_instructions: str | None = None
    ):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.llm_str = llm_str
        self.instructions = default_instructions

    async def generate_responses(self, input_texts: list[str], **kwargs) -> list[str]:
        return await tqdm.gather(
            *[
                self.generate_response(input_text, **kwargs)
                for input_text in input_texts
            ]
        )

    async def generate_response(self, input_text: str, **kwargs) -> str:
        print(f"Generating response for input: {input_text}")
        messages = [create_message("user", input_text)]
        completion = await self.create_completion(messages, **kwargs)
        return completion.choices[0].message.content

    @retry(wait=wait_random_exponential(min=10, max=60), stop=stop_after_attempt(6))
    async def create_completion(self, messages: list[Message], **kwargs) -> Completion:
        instructions = kwargs.pop("instructions", self.instructions)

        if instructions is not None:
            system_message = create_message("system", instructions)
            messages = [system_message, *messages]

        response = await self.client.chat.completions.create(
            model=self.llm_str,
            messages=messages,
            **kwargs,
        )
        return response

    @retry(wait=wait_random_exponential(min=10, max=60), stop=stop_after_attempt(6))
    async def parse_completion(
        self, messages: list[Message], response_format: ResponseFormatT, **kwargs
    ) -> ParsedChatCompletion[ResponseFormatT]:
        instructions = kwargs.pop("instructions", self.instructions)

        if instructions is not None:
            system_message = create_message("system", instructions)
            messages = [system_message, *messages]

        response = await self.client.beta.chat.completions.parse(
            model=self.llm_str,
            messages=messages,
            response_format=response_format,
            **kwargs,
        )
        return response


if __name__ == "__main__":
    llm = LLM()
    message = create_message("user", "Hello, how are you?")
    completion = asyncio.run(llm.create_completion([message]))
    print(completion)

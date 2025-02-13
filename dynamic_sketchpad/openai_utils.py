from io import BytesIO

from IPython.display import Image as IPythonImage
from IPython.display import Markdown, display
from openai import OpenAI
from openai.types.beta.threads import Message, MessageContent
from PIL import Image


def get_strings_from_message(message: Message) -> list[str]:
    return [content.text.value for content in message.content if content.type == "text"]


def get_image_bytes_from_message(client: OpenAI, message: Message) -> list[bytes]:
    return [
        to_image(client, content)
        for content in message.content
        if content.type == "image_file"
    ]


def to_image(client: OpenAI, message_content: MessageContent) -> bytes:
    if message_content.type != "image_file":
        raise ValueError("Message content must be an image file.")

    file_id = message_content.image_file.file_id
    image_data = client.files.content(file_id)
    image_data_bytes = image_data.read()
    return image_data_bytes


def process_message(client: OpenAI, message: Message) -> list[str | bytes]:
    message_contents = []
    for content in message.content:
        if content.type == "image_file":
            message_contents.append(to_image(client, content))
        else:
            message_contents.append(content.text.value)

    return message_contents


def display_message(
    client: OpenAI, message: Message, interactive: bool = False
) -> None:
    for content in message.content:
        if content.type == "image_file":
            image_bytes = to_image(client, content)
            img = Image.open(BytesIO(image_bytes))
            if interactive:
                width, height = img.size
                img.thumbnail((width // 2, height // 2))  # Resize image
                resized_bytes = BytesIO()
                img.save(resized_bytes, format="PNG")
                resized_bytes.seek(0)
                display(IPythonImage(data=resized_bytes.getvalue()))
            else:
                img.show()
        else:
            if interactive:
                display(Markdown(content.text.value))
            else:
                print(content.text.value)

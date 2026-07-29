import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class OpenAIClient:

    def __init__(self):

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY introuvable dans le fichier .env"
            )

        self.client = OpenAI(api_key=api_key)

    def ask(self, prompt: str):

        response = self.client.responses.create(
            model="gpt-5",
            input=prompt,
        )

        return response.output_text
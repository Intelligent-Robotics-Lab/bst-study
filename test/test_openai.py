from openai import OpenAI
import os
from dotenv import load_dotenv
print("SCRIPT STARTED")
load_dotenv()

key = os.getenv("OPENAI_KEY", "").strip()

print("Length:", len(key))
print("Starts:", key[:12])
print("Ends:", key[-8:])
print("Loaded:", key[:15])

client = OpenAI(api_key=key)

response = client.responses.create(
    model="gpt-5-mini",
    input="Say hello"
)

print(response.output_text)
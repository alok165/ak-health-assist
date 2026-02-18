from google import genai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set up the client with API key (new google.genai SDK)
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Define a prompt for the model
prompt = "What is your name?"

# print("the list of models available are:")
# models = client.models.list()

# for model in models:
#     if hasattr(model, 'supported_actions') and "generateContent" in (model.supported_actions or []):
#         print("-", model.name)

#Start a chat session and send a message 
chat = client.chats.create(
    model="gemini-2.0-flash-lite",
    config={"temperature": 0.7},
)
response = chat.send_message(prompt)
print(response.text)
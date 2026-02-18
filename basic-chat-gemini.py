from google import genai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set up the client with API key (new google.genai SDK)
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# System prompt — defines the AI's role and behaviour
SYSTEM_PROMPT = (
    "You are a compassionate health assistant AI. "
    "Your role is to ask the user about their symptoms one at a time, "
    "gather details such as onset, duration, and severity, "
    "then provide possible causes in plain language. "
    "Always remind the user to consult a qualified doctor. "
    "Never diagnose definitively or prescribe medication."
    "If the user mentions any red flag symptoms (e.g., chest pain, severe headache, difficulty breathing), "
    "prompt them to seek immediate medical attention."
    "Use a friendly and empathetic tone throughout the conversation."
    "suggest next steps based on the information provided, such as monitoring symptoms, seeking urgent care, or scheduling a doctor's appointment."
)

# Display system prompt so the developer can see it
print("=" * 60)
print("SYSTEM PROMPT:")
print(SYSTEM_PROMPT)
print("=" * 60)

# Start a chat session with the system prompt passed as system_instruction
chat = client.chats.create(
    model="gemini-2.0-flash-lite",
    config={
        "temperature": 0.7,
        "system_instruction": SYSTEM_PROMPT,
    },
)

# Take user input and send it to the model
user_input = input("\nPlease describe your health concern: ")

# Send the user input to the model and print the response
response = chat.send_message(f"The patient's concern is: {user_input}")
print(f"\nAI Response:\n{response.text}")
# AK Health Assist — Gemini Chat Chatbot

A terminal-based health assistant chatbot powered by Google's Gemini AI. The user describes their health concern and the model responds with relevant information.

---

## Project Structure

```
ak-health-assist/
├── basic-chat-gemini.py   # Main chatbot script
├── requirements.txt       # Python dependencies
├── .env                   # API key (not committed to git)
└── README.md
```

---

## How It Works — Flow

```
┌─────────────────────────────────────────────────────────┐
│                    basic-chat-gemini.py                 │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Load .env file     │  python-dotenv reads GOOGLE_API_KEY
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Create genai       │  google.genai.Client(api_key=...)
│  Client             │
└─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Start Chat Session          │  client.chats.create(
│  model: gemini-2.0-flash-lite│      model=...,
│  temperature: 0.7            │      config={temperature: 0.7}
└──────────────────────────────┘  )
         │
         ▼
┌─────────────────────────────┐
│  Prompt user for input      │  input("Please describe your
│                             │         health concern: ")
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Send message to Gemini     │  chat.send_message(
│                             │      f"The patient's concern
│                             │         is: {user_input}")
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Print AI response          │  print(response.text)
└─────────────────────────────┘
```

---

## Key Concepts Explained

### `google.genai` (New SDK)
The project uses the **new** `google-genai` package (`from google import genai`), not the deprecated `google-generativeai` package. The new SDK uses a `Client` object instead of module-level configuration.

| Old (deprecated)             | New (current)                        |
|------------------------------|--------------------------------------|
| `import google.generativeai` | `from google import genai`           |
| `genai.configure(api_key=…)` | `genai.Client(api_key=…)`            |
| `genai.GenerativeModel(…)`   | `client.chats.create(model=…)`       |
| `model.start_chat()`         | `client.chats.create(…)`             |

### Chat Session
`client.chats.create()` starts a **stateful multi-turn conversation**. Each call to `chat.send_message()` automatically includes the full conversation history, so the model maintains context across turns.

### Temperature (`0.7`)
Controls the randomness of the model's output:
- `0.0` — deterministic, factual responses
- `0.7` — balanced creativity (used here)
- `1.0+` — more creative / varied

### Model: `gemini-2.0-flash-lite`
Chosen because it is the lightest available model with free-tier support. Other available chat-capable models include `gemini-2.0-flash`, `gemini-2.5-flash`, and `gemini-2.5-pro`.

---

## Setup

### 1. Clone the repository
```bash
git clone <repo-url>
cd ak-health-assist
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file
```
GOOGLE_API_KEY=your_api_key_here
```

Get a free API key from [Google AI Studio](https://aistudio.google.com).

### 5. Run the chatbot
```bash
python basic-chat-gemini.py
```

---

## Example Interaction

```
Please describe your health concern: I have a headache and mild fever since morning

The symptoms you describe — headache and mild fever — can be caused by several
common conditions such as a viral infection, dehydration, or tension headache.
Here are some general suggestions:
...
```

---

## Dependencies

| Package         | Purpose                              |
|-----------------|--------------------------------------|
| `google-genai`  | Google Gemini AI SDK (new)           |
| `python-dotenv` | Load API key from `.env` file        |

---

## Notes

- This chatbot is for **informational purposes only** and is not a substitute for professional medical advice.
- Ensure your API key has free-tier access. Keys from [aistudio.google.com](https://aistudio.google.com) include 1500 free requests/day.
- The deprecated `google-generativeai` package is listed (commented out) in `requirements.txt` for reference only.

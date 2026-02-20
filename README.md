# AK Health Assist — Multi-Agent AI Health Chatbot

A terminal-based health assistant powered by **4 specialised Gemini AI agents** that collaborate to conduct a conversational symptom assessment, generate a clinical summary, and save a full audit log of every session.

> **Disclaimer:** This tool is for informational purposes only and is **not** a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified doctor.

---

## Project Structure

```
ak-health-assist/
├── basic-chat-gemini.py   # Main script — 4 agents + orchestrator
├── logs/                  # Auto-created at runtime; one JSON log per session
├── requirements.txt       # Python dependencies
├── .env                   # API key (not committed to git)
└── README.md
```

---

## Architecture — 4 Agents

| Agent | Role | Runs | Gemini API | Temp |
|---|---|---|---|---|
| **Agent 1 — Symptom** | Extracts symptoms, body systems, urgency; flags emergencies | Once on initial input | `generate_content` | 0.3 |
| **Agent 2 — Summary** | Writes a structured 5-7 sentence clinical summary | Once at session end | `generate_content` | 0.4 |
| **Agent 3 — Follow-up** | Stateful chat loop — asks one targeted question per turn | Every turn in loop | `chats.create` | 0.6 |
| **Agent 4 — Audit** | Saves full session as timestamped JSON to `logs/` | Once at session end | File I/O only | — |

---

## How It Works — Full Flow

```
User launches: python basic-chat-gemini.py
         |
         v
+-------------------------------+
|  User describes health concern|
+-------------------------------+
         |
         v
+-------------------------------+
|  Agent 1 - Symptom Analysis   |  Runs once (background)
|  Extracts: primary symptoms,  |  generate_content(), temp=0.3
|  urgency, body systems,       |
|  EMERGENCY flag if needed     |
+-------------------------------+
         | symptom_analysis passed to
         v
+-------------------------------+
|  Agent 3 - Follow-up Chat     |  chats.create(), temp=0.6
|  Seeded with patient complaint|  Maintains full conversation
|  + symptom analysis           |  history automatically
+-------------------------------+
         |
         v
  +============================+
  |   CONVERSATION LOOP        |
  |                            |
  |  Assistant asks question   |
  |          |                 |
  |  User answers              |
  |          |                 |
  |  Repeat until exit         |
  +============================+
         |
         | Exit triggered by:
         | (1) User types: goodbye / bye / exit / quit / stop / end
         | (2) AI says:   "consult a doctor", "human agent",
         |                "seek medical attention", "emergency services"
         v
+-------------------------------+
|  Agent 2 - Summary            |  generate_content(), temp=0.4
|  Clinical summary of the full |
|  conversation (5-7 sentences) |
+-------------------------------+
         |
         v
+-------------------------------+
|  Agent 4 - Audit Log          |
|  Saves JSON to logs/          |
|  health_session_TIMESTAMP.json|
+-------------------------------+
```

---

## Session Exit Conditions

The conversation loop ends when **either** condition is met:

### User-triggered — type any of these at the `You:` prompt:
```
goodbye   bye   exit   quit   stop   end
```

### AI-triggered — assistant closes when its response includes phrases such as:
- `"consult a doctor"` / `"see a doctor"`
- `"human agent"` / `"medical professional"`
- `"seek medical attention"` / `"seek immediate"`
- `"emergency services"` / `"call emergency"`
- `"visit the hospital"` / `"go to the emergency"`

After 4-6 exchanges the assistant naturally closes with a recommendation.

---

## Audit Log Format

Every session is saved to `logs/health_session_YYYYMMDD_HHMMSS.json`:

```json
{
  "conversation": [
    { "role": "user", "content": "I have a headache and fever..." },
    { "role": "assistant", "content": "I'm sorry to hear that. How long have you had the fever?" },
    { "role": "user", "content": "Since this morning, about 6 hours" }
  ],
  "symptom_analysis": "Primary symptoms: headache, fever. Urgency: medium...",
  "final_summary": "The patient presented with headache and fever of 6 hours duration...",
  "session_id": "20260218_143022",
  "logged_at": "2026-02-18T14:30:22.123456"
}
```

---

## SDK Reference — Old vs New

The project uses the **new** `google-genai` package. The old `google-generativeai` is deprecated.

| Old (deprecated) | New (current) |
|---|---|
| `import google.generativeai as genai` | `from google import genai` |
| `genai.configure(api_key=...)` | `genai.Client(api_key=...)` |
| `genai.GenerativeModel(...)` | `client.models.generate_content(model=...)` |
| `model.start_chat()` | `client.chats.create(model=...)` |

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

Get a free API key (1500 req/day) from [Google AI Studio](https://aistudio.google.com).

> Keys from the Google Cloud Console may show `limit: 0` on the free tier. Use AI Studio keys for free-tier access.

### 5. Run the chatbot
```bash
python basic-chat-gemini.py
```

---

## Example Session

```
============================================================
       AK HEALTH ASSIST — Multi-Agent Chatbot
  Agents: Symptom | Follow-up | Summary | Audit
  Type 'exit' or 'goodbye' to end the session.
============================================================
Disclaimer: For informational purposes only.
Always consult a qualified doctor for medical advice.

How are you feeling today? What's your health concern?
> I have a headache and mild fever since this morning

[Agent 1 — Analysing symptoms...]
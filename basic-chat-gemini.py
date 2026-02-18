from google import genai
from dotenv import load_dotenv
import os
import json
import datetime

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = "gemini-2.0-flash-lite"

# Keywords that signal the user wants to end the session
EXIT_KEYWORDS = {"goodbye", "bye", "exit", "quit", "stop", "end"}

# Phrases in AI output that signal it is handing off to professional care
AI_CLOSING_PHRASES = [
    "consult a doctor",
    "see a doctor",
    "seek medical attention",
    "emergency services",
    "human agent",
    "medical professional",
    "visit the hospital",
    "go to the emergency",
    "i recommend you see",
    "please see a",
    "seek immediate",
    "call emergency",
]


def user_wants_to_exit(text: str) -> bool:
    """Check if any exit keyword appears in user input."""
    return any(kw in text.lower().split() for kw in EXIT_KEYWORDS)


def ai_is_closing(text: str) -> bool:
    """Check if AI response contains a handoff / closing phrase."""
    return any(phrase in text.lower() for phrase in AI_CLOSING_PHRASES)


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 1 — Symptom Understanding Agent (runs once on initial input)
# ─────────────────────────────────────────────────────────────────────────────
def symptom_agent(user_input: str) -> str:
    response = client.models.generate_content(
        model=MODEL,
        contents=f"Patient description: {user_input}",
        config={
            "temperature": 0.3,
            "system_instruction": (
                "You are a medical symptom analysis specialist. "
                "Extract primary symptoms, implied symptoms, body systems affected, "
                "and urgency level (low / medium / high / emergency). "
                "If red-flag symptoms are present (chest pain, difficulty breathing, "
                "severe headache, stroke signs), flag as EMERGENCY. "
                "Be structured and brief."
            ),
        },
    )
    return response.text


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 2 — Summarisation Agent (runs at end of session)
# ─────────────────────────────────────────────────────────────────────────────
def summary_agent(conversation: list) -> str:
    history_text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}" for m in conversation
    )
    response = client.models.generate_content(
        model=MODEL,
        contents=f"Full conversation:\n{history_text}",
        config={
            "temperature": 0.4,
            "system_instruction": (
                "You are a medical summarisation specialist. "
                "Write a structured 5-7 sentence clinical summary from the conversation. "
                "Include: chief complaint, symptom details (onset, duration, severity), "
                "follow-up findings, and recommended next steps. "
                "End with a reminder to consult a qualified doctor."
            ),
        },
    )
    return response.text


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 3 — Follow-up / Conversational Agent (stateful chat loop)
# Asks one question at a time; decides when to close and hand off
# ─────────────────────────────────────────────────────────────────────────────
def create_followup_agent():
    """Create and return a stateful follow-up chat session."""
    return client.chats.create(
        model=MODEL,
        config={
            "temperature": 0.6,
            "system_instruction": (
                "You are a compassionate AI health assistant conducting a symptom assessment. "
                "Rules:\n"
                "- Ask ONE targeted question at a time.\n"
                "- Gather: onset, duration, severity (1-10 scale), location, "
                "  associated symptoms, current medications, allergies.\n"
                "- After 4-6 exchanges, OR if symptoms are clearly serious, "
                "  provide a warm closing that:\n"
                "  1) Acknowledges what the patient shared.\n"
                "  2) Suggests next steps (home care / GP / urgent care / emergency).\n"
                "  3) Recommends the patient consult a qualified doctor or human medical agent.\n"
                "- If symptoms sound like an emergency, immediately advise emergency services.\n"
                "- Keep each response to 2-4 sentences. Be warm and empathetic."
            ),
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 4 — Audit / Logging Agent
# ─────────────────────────────────────────────────────────────────────────────
def audit_agent(session_data: dict) -> str:
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/health_session_{timestamp}.json"
    session_data["session_id"] = timestamp
    session_data["logged_at"] = datetime.datetime.now().isoformat()
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)
    return log_file


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR — Runs the full multi-agent session loop
# ─────────────────────────────────────────────────────────────────────────────
def run_health_session():
    session_data: dict = {"conversation": []}
    conversation: list = []

    print("=" * 60)
    print("       AK HEALTH ASSIST — Multi-Agent Chatbot")
    print("  Agents: Symptom | Follow-up | Summary | Audit")
    print("  Type 'exit' or 'goodbye' to end the session.")
    print("=" * 60)
    print("Disclaimer: For informational purposes only.")
    print("Always consult a qualified doctor for medical advice.\n")

    # ── Step 1: Initial complaint ─────────────────────────────────────────────
    initial_input = input("How are you feeling today? What's your health concern?\n> ").strip()

    if not initial_input or user_wants_to_exit(initial_input):
        print("\nGoodbye! Take care and stay healthy.")
        return

    conversation.append({"role": "user", "content": initial_input})
    session_data["conversation"].append({"role": "user", "content": initial_input})

    # ── Step 2: Agent 1 — Symptom analysis (one-time, silent) ────────────────
    print("\n[Agent 1 — Analysing symptoms...]\n")
    symptom_analysis = symptom_agent(initial_input)
    session_data["symptom_analysis"] = symptom_analysis

    # ── Step 3: Agent 3 — Create follow-up chat session ──────────────────────
    followup_chat = create_followup_agent()

    # Seed the follow-up agent with the patient's complaint and analysis
    seed_message = (
        f"The patient described: {initial_input}\n"
        f"Symptom analysis: {symptom_analysis}\n"
        "Acknowledge the patient warmly and ask your first follow-up question."
    )
    first_response = followup_chat.send_message(seed_message)
    ai_message = first_response.text

    print(f"Assistant: {ai_message}")
    conversation.append({"role": "assistant", "content": ai_message})
    session_data["conversation"].append({"role": "assistant", "content": ai_message})

    # ── Step 4: Conversation loop ─────────────────────────────────────────────
    while True:
        # Check if AI has decided to close and hand off
        if ai_is_closing(ai_message):
            print("\n[Session closed — you have been directed to professional care.]")
            break

        user_response = input("\nYou: ").strip()
        if not user_response:
            continue

        conversation.append({"role": "user", "content": user_response})
        session_data["conversation"].append({"role": "user", "content": user_response})

        # User-initiated exit
        if user_wants_to_exit(user_response):
            farewell = (
                "Thank you for sharing with me. Please remember to consult a qualified "
                "doctor or medical professional for proper diagnosis and treatment. "
                "Take care and get well soon!"
            )
            print(f"\nAssistant: {farewell}")
            conversation.append({"role": "assistant", "content": farewell})
            session_data["conversation"].append({"role": "assistant", "content": farewell})
            break

        # Send user response to follow-up agent
        ai_response = followup_chat.send_message(user_response)
        ai_message = ai_response.text
        print(f"\nAssistant: {ai_message}")
        conversation.append({"role": "assistant", "content": ai_message})
        session_data["conversation"].append({"role": "assistant", "content": ai_message})

    # ── Step 5: Agent 2 — Final summary ──────────────────────────────────────
    print("\n" + "─" * 60)
    print("[Agent 2 — Generating session summary...]")
    print("─" * 60)
    final_summary = summary_agent(conversation)
    print(final_summary)
    session_data["final_summary"] = final_summary

    # ── Step 6: Agent 4 — Audit log ──────────────────────────────────────────
    print("\n" + "─" * 60)
    print("[Agent 4 — Saving audit log...]")
    log_file = audit_agent(session_data)
    print(f"Session saved → {log_file}")
    print("─" * 60)
    print("\n" + "=" * 60)
    print("Session complete. Stay well.")
    print("=" * 60)


if __name__ == "__main__":
    run_health_session()

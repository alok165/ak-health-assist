"""AK Health Assist — Streamlit UI
Imports agent logic from basic-chat-gemini.py via importlib
(needed because the filename contains a hyphen).

Run with:
    streamlit run streamlit_app.py
"""

import importlib.util
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


# ── Load basic-chat-gemini.py once and cache it ───────────────────────────────
# Streamlit reruns the full script on every interaction.  Without caching,
# exec_module() would run again each time, creating a new genai.Client and
# closing the previous one — making followup_chat fail with
# "Cannot send a request, as the client has been closed."
@st.cache_resource
def _load_backend():
    _path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "basic-chat-gemini.py")
    spec = importlib.util.spec_from_file_location("basic_chat_gemini", _path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_backend()

# Pull the agent functions and helpers into local names
symptom_agent = _mod.symptom_agent
summary_agent = _mod.summary_agent
create_followup_agent = _mod.create_followup_agent
audit_agent = _mod.audit_agent
user_wants_to_exit = _mod.user_wants_to_exit
ai_is_closing = _mod.ai_is_closing


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AK Health Assist",
    page_icon=":hospital:",
    layout="centered",
)


# ── Session state initialisation ──────────────────────────────────────────────
def _init_state() -> None:
    defaults: dict = {
        "phase": "start",               # "start" | "chat" | "done"
        "conversation": [],             # [{role, content}, …]
        "session_data": {"conversation": []},
        "followup_chat": None,
        "symptom_analysis": "",
        "ai_message": "",               # last AI message (for closing detection)
        "final_summary": "",
        "log_file": "",
        "needs_finalization": False,    # flag to trigger summary + audit
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_state()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("AK Health Assist")
    st.markdown(
        "A multi-agent AI chatbot that guides you through a structured "
        "symptom assessment using Google Gemini."
    )
    st.divider()
    st.markdown("**Agents active in this session**")
    st.markdown(
        "- **Agent 1 — Symptom:** analyses your initial complaint\n"
        "- **Agent 2 — Summary:** produces a clinical recap at the end\n"
        "- **Agent 3 — Follow-up:** asks targeted follow-up questions\n"
        "- **Agent 4 — Audit:** saves a session log to `logs/`"
    )
    st.divider()
    phase_labels = {
        "start": "Waiting to start",
        "chat": "Session active",
        "done": "Session complete",
    }
    st.markdown(f"**Status:** {phase_labels.get(st.session_state.phase, '')}")
    if st.session_state.phase == "chat":
        n_exchanges = len(
            [m for m in st.session_state.conversation if m["role"] == "user"]
        )
        st.markdown(f"**Exchanges:** {n_exchanges}")
    st.divider()
    st.caption(
        "Disclaimer: For informational purposes only. "
        "Always consult a qualified doctor for medical advice."
    )


# ── Main header ───────────────────────────────────────────────────────────────
st.title("AK Health Assist")
st.caption("Multi-Agent AI Health Chatbot — Symptom | Follow-up | Summary | Audit")

st.warning(
    "**Disclaimer:** This tool is for informational purposes only and does not "
    "replace professional medical advice, diagnosis, or treatment.",
    icon="⚠️",
)

st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# PHASE: START — collect initial complaint
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.phase == "start":
    st.subheader("Welcome")
    st.write("Describe your symptoms and I'll guide you through a health assessment.")

    with st.form("initial_form", clear_on_submit=True):
        initial_input = st.text_area(
            "How are you feeling today? What's your health concern?",
            placeholder="e.g. I've had a headache and mild fever since yesterday morning…",
            height=130,
        )
        submitted = st.form_submit_button(
            "Start Assessment", type="primary", use_container_width=True
        )

    if submitted:
        text = initial_input.strip()
        if not text:
            st.warning("Please describe your symptoms before starting.")
        elif user_wants_to_exit(text):
            st.write("Goodbye! Take care and stay healthy.")
        else:
            # Persist initial user message
            st.session_state.conversation.append({"role": "user", "content": text})
            st.session_state.session_data["conversation"].append(
                {"role": "user", "content": text}
            )

            with st.spinner("Analysing symptoms — Agent 1…"):
                analysis = symptom_agent(text)

            st.session_state.symptom_analysis = analysis
            st.session_state.session_data["symptom_analysis"] = analysis

            with st.spinner("Starting follow-up session — Agent 3…"):
                chat = create_followup_agent()
                seed = (
                    f"The patient described: {text}\n"
                    f"Symptom analysis: {analysis}\n"
                    "Acknowledge the patient warmly and ask your first follow-up question."
                )
                first_resp = chat.send_message(seed)
                ai_msg = first_resp.text

            st.session_state.followup_chat = chat
            st.session_state.ai_message = ai_msg
            st.session_state.conversation.append({"role": "assistant", "content": ai_msg})
            st.session_state.session_data["conversation"].append(
                {"role": "assistant", "content": ai_msg}
            )

            st.session_state.phase = "chat"
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PHASE: CHAT — conversation loop
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.phase == "chat":

    # ── Finalization step (triggered by needs_finalization flag) ──────────────
    if st.session_state.needs_finalization:
        st.session_state.needs_finalization = False

        with st.spinner("Generating session summary — Agent 2…"):
            summary = summary_agent(st.session_state.conversation)
        st.session_state.session_data["final_summary"] = summary

        with st.spinner("Saving audit log — Agent 4…"):
            log = audit_agent(st.session_state.session_data)

        st.session_state.final_summary = summary
        st.session_state.log_file = log
        st.session_state.phase = "done"
        st.rerun()
        st.stop()

    # ── Symptom analysis expander ─────────────────────────────────────────────
    if st.session_state.symptom_analysis:
        with st.expander("Symptom Analysis — Agent 1", expanded=False):
            st.markdown(st.session_state.symptom_analysis)

    # ── Render conversation ───────────────────────────────────────────────────
    for msg in st.session_state.conversation:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # ── Chat input ────────────────────────────────────────────────────────────
    user_input = st.chat_input("Type your response…")
    if user_input:
        text = user_input.strip()

        if user_wants_to_exit(text):
            farewell = (
                "Thank you for sharing with me. Please remember to consult a qualified "
                "doctor or medical professional for proper diagnosis and treatment. "
                "Take care and get well soon!"
            )
            for role, content in [("user", text), ("assistant", farewell)]:
                st.session_state.conversation.append({"role": role, "content": content})
                st.session_state.session_data["conversation"].append(
                    {"role": role, "content": content}
                )
            st.session_state.ai_message = farewell
            st.session_state.needs_finalization = True
            st.rerun()

        elif text:
            # Add user message
            st.session_state.conversation.append({"role": "user", "content": text})
            st.session_state.session_data["conversation"].append(
                {"role": "user", "content": text}
            )

            with st.spinner("Thinking…"):
                resp = st.session_state.followup_chat.send_message(text)
                ai_msg = resp.text

            st.session_state.ai_message = ai_msg
            st.session_state.conversation.append({"role": "assistant", "content": ai_msg})
            st.session_state.session_data["conversation"].append(
                {"role": "assistant", "content": ai_msg}
            )

            # Auto-close when AI hands off to professional care
            if ai_is_closing(ai_msg):
                st.session_state.needs_finalization = True

            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PHASE: DONE — show summary and allow restart
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.phase == "done":

    # Symptom analysis
    if st.session_state.symptom_analysis:
        with st.expander("Symptom Analysis — Agent 1", expanded=False):
            st.markdown(st.session_state.symptom_analysis)

    # Full conversation replay
    for msg in st.session_state.conversation:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    st.divider()

    # Clinical summary
    st.subheader("Session Summary — Agent 2")
    st.info(st.session_state.final_summary)

    if st.session_state.log_file:
        st.caption(f"Audit log saved → `{st.session_state.log_file}`")

    st.divider()

    if st.button("Start New Session", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

import streamlit as st
import google.generativeai as genai
import os
import json
import time
from datetime import datetime
from jobs import get_job_links

# If a .env file exists in the project, load simple KEY=VALUE pairs into
# the process environment so the app can pick up PSSKEY/GENAI_API_KEY.
def _load_local_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and v and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass

_load_local_env()

# Try several common environment variable names, then fall back to a
# key stored in Streamlit session state (set via the UI below).
env_key = (
    os.environ.get("PSSKEY")
    or os.environ.get("GENAI_API_KEY")
    or os.environ.get("GOOGLE_API_KEY")
    or os.environ.get("API_KEY")
)

# If a key was loaded from .env into os.environ, propagate it into the
# Streamlit session so the UI reflects that the backend key is present.
try:
    if env_key and ("api_key" not in st.session_state or not st.session_state.get("api_key")):
        st.session_state["api_key"] = env_key
except Exception:
    # If session_state isn't available at import time, ignore.
    pass

# Allow the user to paste an API key into the UI if environment variables
# are not available (useful during local development on Windows).
if "api_key" not in st.session_state:
    st.session_state["api_key"] = None

provided_key = st.session_state.get("api_key") or env_key

if not provided_key:
    st.warning("Backend API key not set. Provide it via environment or paste it securely below.")
    entered = st.text_input("Enter backend API key", type="password")
    if st.button("Set API key") and entered:
        st.session_state["api_key"] = entered
        genai.configure(api_key=entered)
        st.success("API key set for this session. You can now ask questions.")
else:
    # Configure the client once we have a key.
    genai.configure(api_key=provided_key)
    # Attempt to list models once and pick a sensible default so we
    # don't hit 404s for unsupported model names. Store results in
    # session_state to avoid repeated calls which may consume quota.
    try:
        if "available_models" not in st.session_state:
            listed = genai.list_models()
            names = []
            if isinstance(listed, dict):
                candidates = listed.get("models") or listed.get("model") or []
            else:
                candidates = listed
            for item in candidates or []:
                if isinstance(item, dict):
                    n = item.get("name") or item.get("model")
                else:
                    n = getattr(item, "name", None) or getattr(item, "model", None)
                if n:
                    names.append(n)
            st.session_state["available_models"] = names
            # Choose default model: prefer Gemini-family models, fallback to first.
            if names:
                preferred = None
                for n in names:
                    ln = n.lower()
                    if "gemini" in ln and not any(x in ln for x in ("embed", "embedding")):
                        preferred = n
                        break
                if not preferred:
                    # fallback: prefer names that start with 'models/'
                    for n in names:
                        if n.startswith("models/"):
                            preferred = n
                            break
                if not preferred:
                    preferred = names[0]
                # Only set model_name if user hasn't overridden it yet.
                if "model_name" not in st.session_state or not st.session_state.get("model_name"):
                    st.session_state["model_name"] = preferred
    except Exception:
        # Ignore listing errors here; user can click the button in UI.
        pass

# Model selection: allow listing available models from the API and
# selecting one. Default to a common name but let the user override it.
if "model_name" not in st.session_state:
    st.session_state["model_name"] = "text-bison@001"

if provided_key:
    if st.button("List available models"):
        try:
            listed = genai.list_models()
            # Attempt to parse common shapes (list of dicts or objects)
            names = []
            if isinstance(listed, dict):
                # Some SDKs return dict with 'models' key
                candidates = listed.get("models") or listed.get("model") or []
            else:
                candidates = listed

            for item in candidates or []:
                if isinstance(item, dict):
                    n = item.get("name") or item.get("model")
                else:
                    # Try attribute access
                    n = getattr(item, "name", None) or getattr(item, "model", None)
                if n:
                    names.append(n)

            if names:
                st.session_state["available_models"] = names
                st.success(f"Found {len(names)} models. Choose one below.")
            else:
                st.info("No models parsed from API response; check logs.")
                st.write(listed)
        except Exception as e:
            st.error("Could not list models: " + str(e))

    available = st.session_state.get("available_models") or []
    if available:
        choice = st.selectbox("Choose model to use", options=available, index=0)
        st.session_state["model_name"] = choice
    else:
        # Allow manual override if listing not available.
        manual = st.text_input("Model name (override)", value=st.session_state["model_name"])
        st.session_state["model_name"] = manual

else:
    # No key yet — keep default model name but do not attempt to create model.
    st.info("Set API key first to list or select models.")

model = None

st.title("🎓 AI Placement Assistant")
st.write("Ask anything about jobs, placements, skills, interviews")

# Chat/history storage utilities
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "chat_history.json")

def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def append_history(entry):
    h = load_history()
    h.append(entry)
    save_history(h)


# Initialize session state for chat
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = load_history()

# Sidebar: model tools and search
with st.sidebar:
    st.header("Model & Tools")
    st.write("Selected: ", st.session_state.get("model_name"))
    if provided_key:
        if st.button("List available models"):
            try:
                listed = genai.list_models()
                names = []
                if isinstance(listed, dict):
                    candidates = listed.get("models") or listed.get("model") or []
                else:
                    candidates = listed
                for item in candidates or []:
                    if isinstance(item, dict):
                        n = item.get("name") or item.get("model")
                    else:
                        n = getattr(item, "name", None) or getattr(item, "model", None)
                    if n:
                        names.append(n)
                if names:
                    st.session_state["available_models"] = names
                    st.success(f"Found {len(names)} models.")
                else:
                    st.info("No models parsed from API response.")
                    st.write(listed)
            except Exception as e:
                st.error("Could not list models: " + str(e))

        available = st.session_state.get("available_models") or []
        if available:
            choice = st.selectbox("Choose model to use", options=available, index=0)
            st.session_state["model_name"] = choice
        else:
            manual = st.text_input("Model name (override)", value=st.session_state.get("model_name", ""))
            st.session_state["model_name"] = manual

        st.write("")
        if st.button("Test selected model"):
            mn = st.session_state.get("model_name")
            try:
                m = genai.GenerativeModel(mn)
                # small dry-run prompt
                r = m.generate_content("Ping: are you available? Reply short.")
                st.success(f"Model {mn} responded: {getattr(r, 'text', str(r))[:200]}")
            except Exception as e:
                st.error(f"Model test failed: {e}")

        if st.checkbox("Enable safe test of all models (may consume quota)"):
            if st.button("Test all models"):
                results = []
                for mn in st.session_state.get("available_models", []):
                    try:
                        m = genai.GenerativeModel(mn)
                        r = m.generate_content("Ping")
                        results.append({"model": mn, "ok": True, "resp": getattr(r, 'text', str(r))[:200]})
                    except Exception as e:
                        results.append({"model": mn, "ok": False, "error": str(e)})
                st.write(results)

    else:
        st.info("Set API key to list or test models.")

    st.markdown("---")
    st.header("Practice History")
    q = st.text_input("Search history (keyword)")
    if st.button("Show history"):
        hist = st.session_state.get("chat_history", [])
        if q:
            filtered = [h for h in hist if q.lower() in h.get("text", "").lower()]
        else:
            filtered = hist
        for item in filtered[-200:][::-1]:
            ts = item.get("time")
            role = item.get("role")
            model_used = item.get("model")
            st.write(f"[{ts}] ({role}) model={model_used}: {item.get('text')}")

# Main chat area
st.subheader("Conversation")

def render_chat(history):
    for item in history[-200:]:
        ts = item.get("time")
        role = item.get("role")
        if role == "user":
            st.markdown(f"**You** ({ts}): {item.get('text')}")
        else:
            st.markdown(f"**Assistant** ({ts}): {item.get('text')}")

render_chat(st.session_state.get("chat_history", []))

col1, col2 = st.columns([4, 1])
with col1:
    msg = st.text_input("Type your message", key="input_msg")
with col2:
    send = st.button("Send")
    clear = st.button("Clear conversation")

def safe_rerun():
    """Attempt to rerun the Streamlit app. If the running Streamlit
    version doesn't expose experimental_rerun, fall back to changing
    a session-state value which also triggers a rerun in Streamlit.
    """
    try:
        st.experimental_rerun()
    except Exception:
        try:
            # Toggle a session-state value to force a rerun without using
            # deprecated experimental query-param APIs.
            key = "_refresh_toggle"
            if key in st.session_state:
                st.session_state[key] = not st.session_state[key]
            else:
                st.session_state[key] = True
        except Exception:
            pass


if clear:
    st.session_state["chat_history"] = []
    save_history([])
    safe_rerun()

if send and msg:
    if not provided_key:
        st.error("Set API key first.")
    else:
        model_name = st.session_state.get("model_name") or ""
        # append user message
        user_entry = {"role": "user", "text": msg, "time": datetime.utcnow().isoformat(), "model": model_name}
        st.session_state["chat_history"].append(user_entry)
        append_history(user_entry)

        # Build context from last N messages
        ctx_msgs = st.session_state["chat_history"][-6:]
        prompt_parts = ["You are a placement assistant. Keep answers concise."]
        for m in ctx_msgs:
            prefix = "User: " if m.get("role") == "user" else "Assistant: "
            prompt_parts.append(prefix + m.get("text"))
        prompt = "\n\n".join(prompt_parts)

        try:
            # Attempt generation with retries and backoff for quota/errors.
            def is_quota_error(err):
                try:
                    s = str(err)
                    return "quota" in s.lower() or "429" in s
                except Exception:
                    return False

            def generate_with_retries(mn, prompt, attempts=3, base_delay=2.0):
                last_exc = None
                for i in range(attempts):
                    try:
                        mtmp = genai.GenerativeModel(mn)
                        r = mtmp.generate_content(prompt)
                        return getattr(r, "text", str(r)), None
                    except Exception as e:
                        last_exc = e
                        if is_quota_error(e):
                            # exponential backoff based on attempt
                            time.sleep(base_delay * (2 ** i))
                            continue
                        else:
                            return None, e
                return None, last_exc

            text, err = generate_with_retries(model_name, prompt, attempts=3)
            if err and is_quota_error(err):
                # Queue the failed request for later retry.
                pending_file = os.path.join(os.path.dirname(__file__), "pending_requests.json")
                try:
                    pend = []
                    if os.path.exists(pending_file):
                        with open(pending_file, "r", encoding="utf-8") as f:
                            pend = json.load(f)
                except Exception:
                    pend = []
                pend.append({"model": model_name, "prompt": prompt, "time": datetime.utcnow().isoformat()})
                try:
                    with open(pending_file, "w", encoding="utf-8") as f:
                        json.dump(pend, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                # Provide an immediate offline/fallback answer to keep UX smooth.
                text = (
                    "Sorry — the model service quota has been exceeded right now, so I can't produce a live response. "
                    "Here are immediate tips while we retry later:\n\n"
                    "- Create a daily plan: 1 hour aptitude (quant/verbal), 1 hour coding, 30m mock interviews.\n"
                    "- For aptitude: practice arithmetic, percentages, ratios, time & work, permutations, probability.\n"
                    "- Use timed quizzes (30–60 mins) thrice weekly; review mistakes.\n"
                    "- Track progress in a notebook and focus on weakest topics.\n\n"
                    "I saved your query and will retry it later when quota is available."
                )
            elif err:
                text = f"Generation failed: {err}"
        except Exception as e:
            text = f"Generation failed: {e}"

        assistant_entry = {"role": "assistant", "text": text, "time": datetime.utcnow().isoformat(), "model": model_name}
        st.session_state["chat_history"].append(assistant_entry)
        append_history(assistant_entry)
        safe_rerun()

# Job links panel (keep below chat)
st.markdown("---")
st.subheader("Job Links (from query)")
if st.session_state.get("chat_history"):
    last_user = None
    for h in reversed(st.session_state["chat_history"]):
        if h.get("role") == "user":
            last_user = h.get("text")
            break
    if last_user:
        links = get_job_links(last_user)
        if links:
            for link in links:
                st.write(link)
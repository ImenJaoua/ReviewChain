# app.py
import time
import streamlit as st
from chat_env import ChatEnv, ChatEnvConfig
import importlib
phase_module = importlib.import_module("phase")
ReviewPhase = getattr(phase_module, "ReviewPhase")
from agents_local import comment_generator, code_refiner  # ✅ add this import

st.set_page_config(page_title="💬 ReviewChain Dialogue", layout="centered")
st.title("💬 ReviewChain Live Dialogue")

# === Session state ===
if "conversation" not in st.session_state:
    st.session_state.conversation = []

# === Input code snippet ===
initial_code = st.text_area(
    "Paste code snippet to review:",
    """@@ -595,8 +595,10 @@ namespace Kratos
             array_1d<double, 3> b = ZeroVector(3);
             b[0] = 1.0;
 
-            const array_1d<double, 3>  c = MathUtils<double>::CrossProduct(a, b);
-            const array_1d<double, 3>  d = MathUtils<double>::UnitCrossProduct(a, b);
+            array_1d<double, 3>  c, d;
+
+            MathUtils<double>::CrossProduct(c, b, a);
+            MathUtils<double>::UnitCrossProduct(d, b, a);
             
             KRATOS_CHECK_EQUAL(c[2], 2.0);
             KRATOS_CHECK_EQUAL(d[2], 1.0);
"""
)

run_button = st.button("▶️ Start Dialogue")

if run_button:
    st.session_state.conversation = []
    config = ChatEnvConfig(with_memory=False)
    chat_env = ChatEnv(config, initial_code)
    phase = ReviewPhase(chat_env, max_rounds=3)

    # Run the review phase step by step (simulate typing)
    code = chat_env.get("code")
    for round_id in range(phase.max_rounds):
        st.markdown(f"### 🌀 Round {round_id+1}")

        # --- Reviewer ---
        comments = comment_generator(code)
        st.session_state.conversation.append(("Reviewer", comments))
        placeholder = st.empty()
        with placeholder.container():
            st.markdown("**🧑‍💼 Reviewer:**")
            msg = ""
            for ch in comments:
                msg += ch
                placeholder.markdown(f"**🧑‍💼 Reviewer:** {msg}▌")
                time.sleep(0.015)
            placeholder.markdown(f"**🧑‍💼 Reviewer:** {msg}")

        # --- Developer ---
        refined_code = code_refiner(code, comments)
        st.session_state.conversation.append(("Developer", refined_code))
        placeholder = st.empty()
        with placeholder.container():
            st.markdown("**👩‍💻 Developer:**")
            msg = ""
            for ch in refined_code:
                msg += ch
                placeholder.markdown(f"**👩‍💻 Developer:** {msg}▌")
                time.sleep(0.015)
            placeholder.markdown(f"**👩‍💻 Developer:** {msg}")

       
        code = refined_code

st.markdown("---")
st.caption("💡 Powered by your fine-tuned Reviewer & Developer models.")

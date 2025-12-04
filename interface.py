import time
import json
import re
import requests
import streamlit as st

# Backend URL
BACKEND = "http://localhost:8000"

st.set_page_config(page_title="💬 ReviewChain Dialogue", layout="centered")
st.title("💬 ReviewChain Live Dialogue")

# ============================================================
# Backend API wrappers (updated for FEEDBACK support)
# ============================================================

def call_comment_generator(code, feedback=None):
    """Call A1 Reviewer with feedback."""
    try:
        payload = {"code": code, "feedback": feedback}
        res = requests.post(f"{BACKEND}/generate_comment", json=payload, timeout=180)
        res.raise_for_status()
        return res.json()["response"]
    except Exception as e:
        st.error(f"❌ Reviewer error: {e}")
        raise

def call_format_judge(comment):
    try:
        res = requests.post(f"{BACKEND}/format", json={"comment": comment}, timeout=120)
        res.raise_for_status()
        return res.json()["response"]
    except Exception as e:
        st.error(f"❌ Format Judge error: {e}")
        raise

def call_code_refiner(code, comment):
    try:
        payload = {"code": code, "comment": comment}
        res = requests.post(f"{BACKEND}/refine", json=payload, timeout=180)
        res.raise_for_status()
        return res.json()["response"]
    except Exception as e:
        st.error(f"❌ Developer (A2) error: {e}")
        raise

def call_quality_estimator(code):
    try:
        res = requests.post(f"{BACKEND}/quality", json={"code": code}, timeout=180)
        res.raise_for_status()
        return res.json()["response"]
    except Exception as e:
        st.error(f"❌ QE error: {e}")
        raise


# ============================================================
# UI Elements
# ============================================================

initial_code = st.text_area(
    "Enter code to review:",
    """// Paste your code here""",
    height=300
)

col1, col2, col3 = st.columns(3)
with col1:
    max_rounds = st.slider("Maximum rounds:", 1, 20, 10)
with col2:
    max_format_attempts = st.slider("Max format attempts:", 1, 6, 3)
with col3:
    max_quality_attempts = st.slider("Max quality attempts:", 1, 10, 6)

run_button = st.button("▶️ Start Dialogue")

# ============================================================
# MAIN REVIEW LOOP
# ============================================================

if run_button:
    # Check backend connection
    try:
        requests.get(f"{BACKEND}/docs", timeout=2)
        st.success("✅ Connected to backend")
    except:
        st.error(f"❌ Backend unreachable at {BACKEND}. Start backend first:")
        st.code("uvicorn backend:app --reload")
        st.stop()

    current_code = initial_code
    original_code = initial_code   # <--- keep original change

    previous_feedback = None
    format_attempt_count = 0
    quality_attempt_count = 0
    code_accepted = False

    for round_id in range(max_rounds):

        st.markdown(f"## 🌀 Round {round_id + 1}")

        # ==================================================================
        # 1. REVIEWER (A1)
        # ==================================================================
        with st.spinner("🧑‍💼 Reviewer analyzing code..."):
            comments = call_comment_generator(current_code, previous_feedback)

        with st.chat_message("assistant", avatar="🧑‍💼"):
            st.markdown("### 💬 Review Comment")
            st.write(comments)

        # ==================================================================
        # 2. FORMAT JUDGE (A4)
        # ==================================================================
        format_attempt_count += 1

        with st.spinner("📋 Format Judge evaluating..."):
            format_output = call_format_judge(comments)

        # Normalize JSON if necessary
        raw = re.sub(
            r'"decision"\s*:\s*([A-Z]+)',
            r'"decision": "\1"',
            format_output
        )

        try:
            fj = json.loads(raw)
            decision = fj.get("decision", "").upper()
            fj_feedback = fj.get("feedback", "")
            format_accepted = (decision == "ACCEPT")
        except:
            format_accepted = "accept" in format_output.lower()
            fj_feedback = format_output

        with st.chat_message("assistant", avatar="📋"):
            if format_accepted or format_attempt_count >= max_format_attempts:
                if not format_accepted:
                    st.warning("⚠️ Format rejected too many times → bypassing.")
                else:
                    st.success("✅ Format accepted")
                if fj_feedback:
                    st.write(f"Feedback: {fj_feedback}")
            else:
                st.error("❌ Format Rejected")
                st.write(f"Feedback: {fj_feedback}")
                st.info(f"🔄 Reviewer will retry (attempt {format_attempt_count}/{max_format_attempts})")

                # PREPARE FEEDBACK FOR NEXT REVIEWER CALL
                previous_feedback = {
                    "source": "format",
                    "decision": 0,
                    "justification": fj_feedback,
                    "previous_comments": comments,
                    "previous_code": current_code
                }
                continue  # Skip refinement step this round

        # After format accept → reset attempts
        format_attempt_count = 0
        previous_feedback = None

        # ==================================================================
        # 3. DEVELOPER (A2)
        # ==================================================================
        with st.spinner("👩‍💻 Developer refining code..."):
            refined_code = call_code_refiner(current_code, comments)

        current_code = refined_code  # store updated code

        with st.chat_message("user", avatar="👩‍💻"):
            st.markdown("### 🔧 Refined Code")
            st.code(refined_code, language="cpp")

        # ==================================================================
        # 4. QUALITY ESTIMATOR (A3)
        # ==================================================================
        quality_attempt_count += 1

        with st.spinner("🧠 Quality Estimator scoring..."):
            qe_output = call_quality_estimator(refined_code)

        try:
            q = json.loads(qe_output)
            qe_decision = int(q.get("decision", 0))
            justification = q.get("justification", "")
        except:
            qe_decision = 0 if "accept" in qe_output.lower() else 1
            justification = qe_output

        with st.chat_message("assistant", avatar="🧠"):
            if qe_decision == 0:
                st.success("✅ Quality ACCEPTED")
                st.write(justification)
                code_accepted = True
            else:
                st.error("❌ Quality REJECTED")
                st.write(justification)

        # Accepted → stop entirely
        if qe_decision == 0:
            st.balloons()
            break

        # Quality limit reached → force accept
        if quality_attempt_count >= max_quality_attempts:
            st.warning("⚠️ Maximum quality attempts reached → forcing accept.")
            st.balloons()
            code_accepted = True
            break

        # Prepare feedback for next reviewer call
        previous_feedback = {
            "source": "quality",
            "decision": 1,
            "justification": justification,
            "previous_comments": comments,
            "previous_code": current_code
        }

        st.info(f"🔄 Moving to next round (quality attempt {quality_attempt_count}/{max_quality_attempts})")

    # ============================================================
    # FINAL SUMMARY
    # ============================================================
    st.markdown("---")
    st.markdown("## 📊 Final Summary")

    col1, col2 = st.columns(2)
    col1.metric("Total Rounds", round_id + 1)
    col2.metric("Status", "Accepted" if code_accepted else "Forced Accept")

    st.markdown("### 📄 Final Code")
    st.code(current_code, language="cpp")

    st.download_button(
        "💾 Download Final Code",
        current_code,
        file_name="final_code.cpp",
        mime="text/plain"
    )

st.caption("💡 Powered by your Reviewer, Format Judge, Developer & Quality Estimator models via backend API.")

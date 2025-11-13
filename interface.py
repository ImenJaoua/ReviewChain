# app.py
import time
import json
import streamlit as st
from chat_env import ChatEnv, ChatEnvConfig
import importlib
phase_module = importlib.import_module("phase")
ReviewPhase = getattr(phase_module, "ReviewPhase")
from agents_local import comment_generator, code_refiner, quality_estimator

st.set_page_config(page_title="💬 ReviewChain Dialogue", layout="centered")
st.title("💬 ReviewChain Live Dialogue")

# === Session state ===
if "conversation" not in st.session_state:
    st.session_state.conversation = []

# === Input code snippet ===
initial_code = st.text_area(
    "Enter code to review:",
    """// Paste your code here""",
    height=300
)

max_rounds = st.slider("Maximum rounds:", min_value=1, max_value=10, value=5)
run_button = st.button("▶️ Start Dialogue")

if run_button:
    st.session_state.conversation = []
    config = ChatEnvConfig(with_memory=False)
    chat_env = ChatEnv(config, initial_code)
    
    # Variables for feedback loop
    original_code = initial_code
    current_code = original_code
    code_accepted = False

    # Run the review phase step by step
    for round_id in range(max_rounds):
        st.markdown(f"### 🌀 Round {round_id+1}/{max_rounds}")
        
        # --- Step 1: Reviewer ---
        # Always review the current code (not original)
        comments = comment_generator(current_code)
        
        st.session_state.conversation.append(("Reviewer", comments))
        
        with st.chat_message("assistant", avatar="🧑‍💼"):
            st.markdown("**💬 Review Comment:**")
            msg_placeholder = st.empty()
            msg = ""
            for ch in comments:
                msg += ch
                msg_placeholder.markdown(msg + "▌")
                time.sleep(0.01)
            msg_placeholder.markdown(msg)

        # --- Step 2: Developer ---
        refined_code = code_refiner(current_code, comments)
        current_code = refined_code
        st.session_state.conversation.append(("Developer", refined_code))
        
        with st.chat_message("user", avatar="👩‍💻"):
            st.markdown("**🔧 Refined Code:**")
            code_placeholder = st.empty()
            displayed_code = ""
            
            # Display code in chunks for better visualization
            lines = refined_code.split('\n')
            for line in lines:
                displayed_code += line + '\n'
                code_placeholder.code(displayed_code, language="cpp")
                time.sleep(0.05)

        # --- Step 3: Quality Estimator ---
        with st.spinner("🧠 Quality Estimator analyzing..."):
            time.sleep(0.5)  # Brief pause for effect
            estimated_quality = quality_estimator(refined_code)
        
        st.session_state.conversation.append(("QualityEstimator", estimated_quality))
        
        # Parse the quality result
        try:
            result = json.loads(estimated_quality)
            decision = int(result.get("decision", 0))
            justification = result.get("justification", "")
        except Exception as e:
            st.error(f"⚠️ Could not parse Quality Estimator output: {e}")
            # Try text parsing as fallback
            decision = 0
            justification = estimated_quality
            if "Decision: 1" in estimated_quality or "decision: 1" in estimated_quality.lower():
                decision = 1
        
        # Display quality estimator result
        with st.chat_message("assistant", avatar="🧠"):
            if decision == 1:
                st.success("✅ **Code ACCEPTED**")
                st.markdown(f"**Justification:** {justification}")
                code_accepted = True
            else:
                st.error("❌ **Code REJECTED**")
                st.markdown(f"**Justification:** {justification}")
        
        # Check if code is accepted
        if decision == 1:
            st.balloons()
            st.success(f"🎉 Code accepted in round {round_id + 1}!")
            break
        else:
            if round_id == max_rounds - 1:
                st.warning(f"⚠️ Maximum rounds ({max_rounds}) reached without acceptance.")
            else:
                st.info("🔄 Moving to next round...")
                time.sleep(1)

    # === Final Summary ===
    st.markdown("---")
    st.markdown("### 📊 Final Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Rounds", round_id + 1)
    with col2:
        st.metric("Status", "✅ Accepted" if code_accepted else "❌ Not Accepted")
    with col3:
        st.metric("Conversations", len(st.session_state.conversation))
    
    # Show final code
    with st.expander("📄 View Final Code", expanded=False):
        st.code(current_code, language="cpp")
    
    # Download conversation log
    if st.button("💾 Download Conversation Log"):
        conversation_json = json.dumps(st.session_state.conversation, indent=2)
        st.download_button(
            label="Download JSON",
            data=conversation_json,
            file_name="review_conversation.json",
            mime="application/json"
        )

st.markdown("---")
st.caption("💡 Powered by your fine-tuned Reviewer, Developer & Quality Estimator models.")
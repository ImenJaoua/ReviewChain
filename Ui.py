import streamlit as st
from autogen_agnets import run_review_session  # Import your function
import time

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'current_round' not in st.session_state:
    st.session_state.current_round = 0
if 'review_started' not in st.session_state:
    st.session_state.review_started = False

# Page config
st.set_page_config(page_title="Multi-Agent Code Review", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .reviewer-msg {
        background-color: #eff6ff;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #2563eb;
        margin: 10px 0;
        color: #1e3a8a;
    }
    .developer-msg {
        background-color: #f0fdf4;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #16a34a;
        margin: 10px 0;
        color: #14532d;
    }
    .qualityestimator-msg {
        background-color: #faf5ff;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #9333ea;
        margin: 10px 0;
        color: #581c87;
    }
    .commentjudge-msg {
        background-color: #fff7ed;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #ea580c;
        margin: 10px 0;
        color: #7c2d12;
    }
    .system-msg {
        background-color: #f3f4f6;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
        margin: 15px 0;
        color: #374151;
    }
    .stTextArea textarea {
        font-family: monospace;
    }
    .agent-content {
        color: inherit;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🤖 Multi-Agent Code Review System")
st.markdown("**4 AI agents collaborating on code quality**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    initial_code = st.text_area(
        "Initial Code",
        value="""def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total""",
        height=200,
        help="Enter the code to review"
    )
    
    old_code = st.text_area(
        "Old Code (Optional)",
        value="",
        height=100,
        help="Previous version of the code for comparison"
    )
    
    st.markdown("---")
    
    max_rounds = st.slider("Max Rounds", 1, 5, 3)
    reviewer_tokens = st.slider("Reviewer Max Tokens", 128, 1024, 512)
    developer_tokens = st.slider("Developer Max Tokens", 128, 1024, 512)
    
    st.markdown("---")
    st.header("🎨 Agent Legend")
    st.markdown("🔵 **Reviewer** - Analyzes code quality")
    st.markdown("🟢 **Developer** - Refines code based on feedback")
    st.markdown("🟣 **Quality Estimator** - Evaluates improvements")
    st.markdown("🟠 **Comment Judge** - Makes final judgment")

# Main content
col1, col2 = st.columns([3, 1])

with col1:
    st.header("💬 Agent Conversation")

with col2:
    start_button = st.button(
        "▶️ Start Review", 
        disabled=st.session_state.is_running, 
        use_container_width=True,
        type="primary"
    )
    
    reset_button = st.button(
        "🔄 Reset", 
        use_container_width=True
    )

if reset_button:
    st.session_state.messages = []
    st.session_state.is_running = False
    st.session_state.current_round = 0
    st.session_state.review_started = False
    st.rerun()

if start_button:
    st.session_state.is_running = True
    st.session_state.messages = []
    st.session_state.current_round = 0
    st.session_state.review_started = True

# Chat container - create placeholder for live updates
chat_container = st.container()

# Create a placeholder for messages that updates live
message_placeholder = chat_container.empty()

def render_messages():
    """Render all messages in the placeholder"""
    with message_placeholder.container():
        if not st.session_state.messages:
            st.info("👆 Click 'Start Review' to begin the agent conversation")
        else:
            for i, msg in enumerate(st.session_state.messages):
                st.markdown(f"""
                <div class="{msg['style']}">
                    <strong>{msg['agent']}</strong>
                    {f'<span style="float:right; font-size:0.8em;">Round {msg["round"]}</span>' if msg['round'] > 0 else ''}
                    <br><br>
                    <div class="agent-content" style="white-space: pre-wrap; font-family: monospace; font-size: 0.9em;">
                    {msg['content'][:500]}{'...' if len(msg['content']) > 500 else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# Callback function to capture messages from agents
def message_callback(agent_name: str, content: str, round_num: int):
    """
    Callback function that gets called by run_review_session
    to send messages to the UI
    """
    st.session_state.current_round = round_num
    
    # Determine style class based on agent name
    style_class = f"{agent_name.lower()}-msg"
    
    # Add message to session state
    st.session_state.messages.append({
        'agent': agent_name,
        'content': content,
        'style': style_class,
        'round': round_num
    })
    
    # Update the display immediately
    render_messages()

# Display initial state
if not st.session_state.review_started or not st.session_state.is_running:
    render_messages()

# Run the review session
if st.session_state.is_running and st.session_state.review_started:
    # Show progress indicator
    progress_placeholder = st.empty()
    progress_placeholder.info(f"🔄 Running multi-agent code review...")
    
    try:
        # Call your actual run_review_session function
        result = run_review_session(
            initial_code=initial_code,
            max_rounds=max_rounds,
            reviewer_max_tokens=reviewer_tokens,
            developer_max_tokens=developer_tokens,
            old_code=old_code,
            message_callback=message_callback  # Pass the callback
        )
        
        progress_placeholder.success("✅ Code review completed successfully!")
        
    except Exception as e:
        progress_placeholder.error(f"❌ Error during review: {str(e)}")
        st.exception(e)
        # Print full traceback for debugging
        import traceback
        st.code(traceback.format_exc())
    finally:
        st.session_state.is_running = False
        st.session_state.review_started = False
        # Final render
        render_messages()

# Show statistics in sidebar if review has run
if st.session_state.messages:
    with st.sidebar:
        st.markdown("---")
        st.header("📊 Session Stats")
        st.metric("Total Messages", len(st.session_state.messages))
        st.metric("Rounds Completed", st.session_state.current_round)
        
        # Count messages per agent
        agent_counts = {}
        for msg in st.session_state.messages:
            agent = msg['agent']
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        st.markdown("**Messages per Agent:**")
        for agent, count in agent_counts.items():
            if agent != "System":
                st.text(f"{agent}: {count}")
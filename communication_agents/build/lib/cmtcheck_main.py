# main.py
from chat_env import ChatEnv, ChatEnvConfig
from phase import ReviewPhase

def main(initial_code=None):
    print("🚀 Starting ReviewChain System...\n")

    # --- Configuration ---
    config = ChatEnvConfig(with_memory=True, test_enabled=True)

    chat_env = ChatEnv(config, initial_code)

    # --- Run one review phase ---
    phase = ReviewPhase(chat_env, max_rounds=3)
    final_code = phase.execute()

    print("\n✅ ReviewChain session complete.")

    return final_code

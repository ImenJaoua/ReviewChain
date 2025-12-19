# main.py
from chat_env import ChatEnv, ChatEnvConfig
from phase import ReviewPhase

def main(initial_code=None):
    # --- Configuration ---
    config = ChatEnvConfig(with_memory=True, test_enabled=True)

    chat_env = ChatEnv(config, initial_code)

    # --- Run one review phase ---
    phase = ReviewPhase(chat_env, max_rounds=3)
    final_code, final_comment = phase.execute()

    print("\n" + "=" * 80)

    BOLD_CYAN = "\033[1;36m"
    RESET = "\033[0m"

    print(f"{BOLD_CYAN}\n📝 Final Accepted Comment:\n{RESET}")

    print(final_comment)

    print("=" * 80 + "\n")

    print("\n✅ ReviewChain session complete.")

    return final_code

# main.py
from chat_env import ChatEnv, ChatEnvConfig
from phase import ReviewPhase

if __name__ == "__main__":
    print("🚀 Starting ReviewChain System...\n")

    # --- Configuration ---
    config = ChatEnvConfig(with_memory=True, test_enabled=True)

    # --- Initialize environment ---
    initial_code = """ @@ -41,11 +41,22 @@
 	@NotBlank
 	private String composedTaskRunnerName = "composed-task-runner";
 
+	@NotBlank
+	private String schedulerTaskLauncher = "scheduler-task-launcher";
"""
    
    chat_env = ChatEnv(config, initial_code)

    # --- Run one review phase ---
    phase = ReviewPhase(chat_env, max_rounds=5)
    final_code = phase.execute()

    # --- Save and print results ---
    chat_env.export_history()
    print("\n✅ Final refined code:\n", final_code)
    print("\n🧠 Memory stored in:", chat_env.memory.filename)
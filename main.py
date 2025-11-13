# main.py
from chat_env import ChatEnv, ChatEnvConfig
from phase import ReviewPhase

if __name__ == "__main__":
    print("🚀 Starting ReviewChain System...\n")

    # --- Configuration ---
    config = ChatEnvConfig(with_memory=True, test_enabled=True)

    # --- Initialize environment ---
    initial_code = """ @@ -2633,22 +2537,26 @@ func operatorPod(podName, appName, operatorServiceIP, agentPath, operatorImagePa
 
 // operatorConfigMap returns a *core.ConfigMap for the operator pod
 // of the specified application, with the specified configuration.
-func operatorConfigMap(appName, operatorName string, config *caas.OperatorConfig) *core.ConfigMap {
-	configMapName := operatorConfigMapName(operatorName)
+func operatorConfigMap(appName, cmName string, labels map[string]string, config *caas.OperatorConfig) *core.ConfigMap {
"""
    chat_env = ChatEnv(config, initial_code)

    # --- Run one review phase ---
    phase = ReviewPhase(chat_env, max_rounds=3)
    final_code = phase.execute()

    # --- Save and print results ---
    chat_env.export_history()
    print("\n✅ Final refined code:\n", final_code)
    print("\n🧠 Memory stored in:", chat_env.memory.filename)
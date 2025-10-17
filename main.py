# main.py
from chat_env import ChatEnv, ChatEnvConfig
from phase import ReviewPhase

if __name__ == "__main__":
    print("🚀 Starting ReviewChain System...\n")

    # --- Configuration ---
    config = ChatEnvConfig(with_memory=True, test_enabled=True)

    # --- Initialize environment ---
    initial_code = """ @@ -595,8 +595,10 @@ namespace Kratos
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
    chat_env = ChatEnv(config, initial_code)

    # --- Run one review phase ---
    phase = ReviewPhase(chat_env, max_rounds=3)
    final_code = phase.execute()

    # --- Save and print results ---
    chat_env.export_history()
    print("\n✅ Final refined code:\n", final_code)
    print("\n🧠 Memory stored in:", chat_env.memory.filename)

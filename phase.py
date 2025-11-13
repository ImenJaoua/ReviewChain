# phase.py
import json
from chat_env import ChatEnv
from agents_local import comment_generator, code_refiner, quality_estimator


class ReviewPhase:
    """
    One phase of collaboration between Reviewer (A1) and Developer (A2).
    Handles multiple review rounds until code passes tests or is approved.
    """

    def __init__(self, chat_env: ChatEnv, max_rounds=5):
        self.chat_env = chat_env
        self.max_rounds = max_rounds

    def execute(self):
        """Run iterative dialogue between A1 and A2."""
        original_code = self.chat_env.get("code")
        current_code = original_code
        previous_feedback = None  # Will store quality estimator feedback

        for round_id in range(self.max_rounds):
            print(f"\n{'='*60}")
            print(f"=== ROUND {round_id + 1}/{self.max_rounds} ===")
            print(f"{'='*60}")
            
            # --- Step 1: Reviewer (A1) ---
            # First round: use original code
            # Subsequent rounds: use original code + feedback from quality estimator
            if round_id == 0:
                comments = comment_generator(original_code)
            else:
                # Generate comments with feedback context
                comments = comment_generator(
                    feedback=previous_feedback,
                )
            self.chat_env.update("comments", comments)
            self.chat_env.append_history("Reviewer", comments)
            print("\n💬 Reviewer:\n", comments)

            # --- Step 2: Developer (A2)
            refined_code = code_refiner(current_code, comments)
            current_code = refined_code
            self.chat_env.update_code(refined_code)
            self.chat_env.append_history("Developer", refined_code)
            print("\n🧑‍💻 Developer:\n", refined_code)

            estimated_quality = quality_estimator(refined_code)
            print("\n🧠 Quality Estimator:\n", estimated_quality)
             # === Step 4: Parse JSON safely
            try:
                result = json.loads(estimated_quality)
                decision = int(result.get("decision", 0))
                justification = result.get("justification", "")
            except Exception as e:
                print(f"⚠️ Could not parse JSON from estimator output: {e}")

            # Store feedback for next round
            previous_feedback = {
                "decision": decision,
                "justification": justification,
                "previous_comments": comments,
                "previous_code": current_code
            }
            # Check if code is accepted
            if decision == 1:
                print(f"\n✅ Code ACCEPTED in round {round_id + 1}!")
                self.chat_env.append_history("QualityEstimator", f"ACCEPTED: {justification}")
                break
            else:
                print(f"\n❌ Code REJECTED in round {round_id + 1}")
                self.chat_env.append_history("QualityEstimator", f"REJECTED: {justification}")
                
                if round_id == self.max_rounds - 1:
                    print(f"\n⚠️ Maximum rounds ({self.max_rounds}) reached without acceptance.")
            self.chat_env.next_iteration()



        print("\n📄 Final Code:\n", self.chat_env.get_code())
        return self.chat_env.get_code()

import json
from chat_env import ChatEnv
from agents_local import (
    comment_generator,
    code_refiner,
    quality_estimator
)


class ReviewPhase:
    """
    ONE-SHOT REVIEW PIPELINE

    PHASE 1: A1 → comment generation
    PHASE 2: A2 → refinement
    PHASE 3: A3 → quality estimation

    No retries, no loops, no feedback in a second round.
    """

    def __init__(self, chat_env: ChatEnv):
        self.chat_env = chat_env


    def execute(self):
        # ----------------------------------------------
        # Load the initial code
        # ----------------------------------------------
        current_code = self.chat_env.get("code")
        print("\nInitial Code:\n", current_code)

        # ----------------------------------------------
        # PHASE 1: Comment Generation (A1)
        # ----------------------------------------------
        print("\n--- Phase 1: Comment Generation (A1) ---")

        comment = comment_generator(
            code_diff=current_code,
            feedback=None        # single round → no previous feedback
        )

        print("\n💬 A1 Comment:")
        print(comment)

        self.chat_env.append_history("Reviewer", comment)
        self.chat_env.update("comments", comment)

        # ----------------------------------------------
        # PHASE 2: Code Refinement (A2)
        # ----------------------------------------------
        print("\n--- Phase 2: Refinement (A2) ---")

        refined_code = code_refiner(current_code, comment)

        print("\n🛠 A2 Refined Code:")
        print(refined_code)

        self.chat_env.append_history("Developer", refined_code)

        # ----------------------------------------------
        # PHASE 3: Quality Estimation (A3)
        # ----------------------------------------------
        print("\n--- Phase 3: Quality Estimation (A3) ---")

        qe_output = quality_estimator(refined_code)
        print("\n🧠 A3 Response:")
        print(qe_output)

        # Best-effort parse
        try:
            q = json.loads(qe_output)
            qe_decision = int(q.get("decision", 0))
            qe_feedback = q.get("justification", "")
        except:
            qe_decision = 0 if "accept" in qe_output.lower() else 1
            qe_feedback = qe_output

        # ----------------------------------------------
        # Final result
        # ----------------------------------------------
        if qe_decision == 0:
            print("\n🎉 QUALITY ACCEPTED!")
        else:
            print("\n❌ QUALITY REJECTED!")
            print("Reason:", qe_feedback)

        # Save final result (even if rejected)
        self.chat_env.update_code(refined_code)
        self.chat_env.append_history("QualityEstimator", "ACCEPTED" if qe_decision == 0 else "REJECTED")

        print("\n=== FINAL SUMMARY ===")
        print("Final code:\n", refined_code)

        return refined_code

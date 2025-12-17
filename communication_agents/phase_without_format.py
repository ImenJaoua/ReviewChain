import json
from chat_env import ChatEnv
from course_project.reviewchain.communication_agents.agents_local import (
    comment_generator,
    code_refiner,
    quality_estimator
)


class ReviewPhase:
    """
    Simplified two-step pipeline WITHOUT format judge:

    PHASE 1:
        A1 → comment generation

    PHASE 2:
        A2 → refinement
        A3 → quality estimation

    If A3 rejects:
        → feedback returned to A1, loop

    If A3 accepts:
        → DONE

    Limits:
        - Quality Estimator attempts: 6
    """

    def __init__(self, chat_env: ChatEnv, max_rounds=20):
        self.chat_env = chat_env
        self.max_rounds = max_rounds
        self.max_quality_attempts = 6


    def execute(self):
        current_code = self.chat_env.get("code")
        print(current_code)

        previous_feedback = None
        quality_attempt_count = 0

        for round_id in range(self.max_rounds):

            print(f"\n{'='*70}")
            print(f"=== ROUND {round_id + 1}/{self.max_rounds} ===")
            print(f"Quality attempts: {quality_attempt_count}/{self.max_quality_attempts}")
            print(f"{'='*70}")

            # =====================================================
            # PHASE 1: Comment Generation (A1)
            # =====================================================
            print("\n--- Phase 1: Comment Generation (A1) ---")

            comment = comment_generator(
                code_diff=current_code,
                feedback=previous_feedback
            )

            print("\n💬 A1 Comment:")
            print(comment)
            self.chat_env.append_history("Reviewer", comment)
            self.chat_env.update("comments", comment)

            # =====================================================
            # PHASE 2: Code Refinement (A2)
            # =====================================================
            print("\n--- Phase 2: Refinement (A2) ---")

            proposed_code = code_refiner(current_code, comment)

            print("\n🛠 A2 Refined Code:")
            print(proposed_code)

            self.chat_env.append_history("Developer", proposed_code)

            # =====================================================
            # PHASE 3: Quality Estimation (A3)
            # =====================================================
            print("\n--- Phase 3: Quality Estimation (A3) ---")

            quality_attempt_count += 1

            qe_output = quality_estimator(proposed_code)
            print("\n🧠 A3 Response:")
            print(qe_output)

            # Parse QE JSON safely
            try:
                q = json.loads(qe_output)
                qe_decision = int(q.get("decision", 0))
                qe_feedback = q.get("justification", "")
            except:
                qe_decision = 0 if "accept" in qe_output.lower() else 1
                qe_feedback = qe_output

            # =====================================================
            # If QE REJECTS → retry from A1
            # =====================================================
            if qe_decision == 1:
                if quality_attempt_count >= self.max_quality_attempts:
                    print(f"\n⚠️ QUALITY CHECK LIMIT REACHED — forcing acceptance")
                    qe_decision = 0
                else:
                    #current_code= proposed_code  # keep last proposed code for next round
                    print("\n❌ QE REJECTED — looping back to A1")

                    previous_feedback = {
                        "source": "quality",
                        "decision": 1,
                        "justification": qe_feedback,
                        "previous_comments": comment,
                        "previous_code": current_code  # old code
                    }

                    continue  # restart at Phase 1

            # =====================================================
            # QE ACCEPTED → finish
            # =====================================================
            print("\n🎉 FINAL: QUALITY ACCEPTED!")
            current_code = proposed_code
            self.chat_env.update_code(proposed_code)
            self.chat_env.append_history("QualityEstimator", "ACCEPTED")
            break

        # =========================================================
        # FINAL SUMMARY
        # =========================================================
        print("\n=== FINAL SUMMARY ===")
        print(f"Total quality attempts: {quality_attempt_count}")
        print("Final code:\n", self.chat_env.get_code())

        return self.chat_env.get_code()

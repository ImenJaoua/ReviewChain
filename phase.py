import json
import re
from chat_env import ChatEnv
from agents_local import (
    comment_generator,
    code_refiner,
    quality_estimator,
    format_judge
)


class ReviewPhase:
    """
    Two-phase pipeline with NO conversation history:

    PHASE 1 (Format Loop):
        A1 → A4 (Format Judge)
        
        If A4 rejects:
            → feedback to A1 (loop continues in Phase 1)
        
        If A4 accepts:
            → Move to PHASE 2

    PHASE 2 (Quality Loop):
        A2 → A3 (Quality Estimator)
        
        If A3 rejects:
            → feedback to A1 (back to Phase 1)
        
        If A3 accepts:
            → FINISH
    
    Each call to A1 is independent - no history is maintained.
    
    Limits:
        - Format checks: Maximum 3 attempts
        - Quality estimator: Maximum 5 attempts
    """

    def __init__(self, chat_env: ChatEnv, max_rounds=20):
        self.chat_env = chat_env
        self.max_rounds = max_rounds
        self.max_format_attempts = 3
        self.max_quality_attempts = 6


    def execute(self):
        current_code = self.chat_env.get("code")
        print(current_code)
        previous_feedback = None
        
        format_attempt_count = 0
        quality_attempt_count = 0

        for round_id in range(self.max_rounds):

            print(f"\n{'='*70}")
            print(f"=== ROUND {round_id + 1}/{self.max_rounds} ===")
            print(f"Format attempts: {format_attempt_count}/{self.max_format_attempts} | Quality attempts: {quality_attempt_count}/{self.max_quality_attempts}")
            print(f"{'='*70}")

            # =====================================================
            # PHASE 1: Comment Generation + Format Check
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
            # Format Judge (A4) - Check comment format
            # =====================================================
            print("\n--- Phase 1.5: Format Check (A4) ---")
            
            format_attempt_count += 1

            format_output = format_judge(comment)
            print("\n📋 A4 Format Judge Response:")
            print(format_output)

            # Parse format judge JSON
            # Fix invalid JSON: "decision": ACCEPT → "decision": "ACCEPT"
            raw = re.sub(
                r'"decision"\s*:\s*([A-Z]+)',
                r'"decision": "\1"',
                format_output
            )

            # Parse JSON safely
            try:
                fj = json.loads(raw)
                fj_decision_raw = fj.get("decision", "").strip().upper()
                fj_feedback = fj.get("feedback", "").strip()
            except Exception:
                fj_decision_raw = "REJECT"
                fj_feedback = format_output

            # Convert to boolean (ONLY ACCEPT / REJECT)
            fj_accept = (fj_decision_raw == "ACCEPT")

            print("\nParsed Format Judge Decision:", "ACCEPT" if fj_accept else "REJECT")

            # =====================================================
            # If Format Judge REJECTS → check limit then back to A1
            # =====================================================
            if not fj_accept:
                if format_attempt_count >= self.max_format_attempts:
                    print(f"\n⚠️ FORMAT CHECK LIMIT REACHED ({self.max_format_attempts} attempts) — proceeding with current comment")
                    self.chat_env.append_history("FormatJudge", f"REJECTED (limit reached): {fj_feedback}")
                    # Force accept and continue to Phase 2
                    fj_accept = True
                else:
                    print(f"\n❌ FORMAT REJECTED — looping back to A1 (attempt {format_attempt_count}/{self.max_format_attempts})")

                    previous_feedback = {
                        "source": "format",
                        "decision": 0,
                        "justification": fj_feedback,
                        "previous_comments": comment,
                        "previous_code": current_code
                    }

                    self.chat_env.append_history("FormatJudge", f"REJECTED: {fj_feedback}")
                    continue  # Restart loop at Phase 1

            # =====================================================
            # Format ACCEPTED → Move to Phase 2
            # =====================================================

            print("\n✅ FORMAT ACCEPTED — moving to refinement phase")
            self.chat_env.append_history("FormatJudge", "ACCEPTED")
            
            # Reset format counter for next quality loop iteration
            format_attempt_count = 0

            # =====================================================
            # PHASE 2: Code Refinement (A2)
            # =====================================================
            print("\n--- Phase 2: Refinement (A2) ---")

            proposed_code = code_refiner(current_code, comment)

            print("\n🛠 A2 Refined Code:")
            print(proposed_code)

            # Do NOT update current_code yet
            self.chat_env.append_history("Developer", proposed_code)

            # =====================================================
            # PHASE 2.5: Quality Estimation (A3)
            # =====================================================
            print("\n--- Phase 2.5: Quality Estimation (A3) ---")

            quality_attempt_count += 1

            # Quality estimator MUST inspect the newly refined code
            qe_output = quality_estimator(proposed_code)
            print("\n🧠 A3 Response:")
            print(qe_output)

            # Parse QE output
            try:
                q = json.loads(qe_output)
                qe_decision = int(q.get("decision", 0))
                qe_feedback = q.get("justification", "")
            except:
                qe_decision = 0 if "accept" in qe_output.lower() else 1
                qe_feedback = qe_output

            # =====================================================
            # If QE REJECTS → do not update current_code
            # =====================================================
            if qe_decision == 1:
                if quality_attempt_count >= self.max_quality_attempts:
                    print(f"\n⚠️ QUALITY CHECK LIMIT REACHED — accepting proposed code")
                    qe_decision = 0  # force accept
                else:
                    print("\n❌ QE REJECTED — returning to Phase 1 without updating current_code")

                    previous_feedback = {
                        "source": "quality",
                        "decision": 1,
                        "justification": qe_feedback,
                        "previous_comments": comment,
                        "previous_code": current_code   # still the old code!
                    }

                    continue      # go back to phase 1 with old code

            # =====================================================
            # QE ACCEPTED → commit refined code
            # =====================================================
            print("\n🎉 FINAL: FORMAT AND QUALITY BOTH ACCEPTED!")
            current_code = proposed_code         # ← NOW we update it
            self.chat_env.update_code(proposed_code)
            self.chat_env.append_history("QualityEstimator", "ACCEPTED")
            break

        # Final summary
        print("\n=== FINAL SUMMARY ===")
        print(f"Total format attempts: {format_attempt_count}")
        print(f"Total quality attempts: {quality_attempt_count}")
        print("Final code:\n", self.chat_env.get_code())
        return self.chat_env.get_code()
# phase_backend.py
import json
import re
import requests
from chat_env import ChatEnv

BACKEND = "http://localhost:8000"

class ReviewPhase:

    def __init__(self, chat_env: ChatEnv, max_rounds=20):
        self.chat_env = chat_env
        self.max_rounds = max_rounds
        self.max_format_attempts = 3
        self.max_quality_attempts = 6

    # -----------------------------
    # Backend wrappers
    # -----------------------------
    def a1_comment(self, code, feedback=None):
        """Call A1 through backend"""
        payload = {"code": code, "feedback": feedback}
        res = requests.post(f"{BACKEND}/generate_comment", json=payload)
        return res.json()["response"]

    def a4_format_judge(self, comment):
        res = requests.post(f"{BACKEND}/format", json={"comment": comment})
        return res.json()["response"]

    def a2_refine(self, code, comment):
        payload = {"code": code, "comment": comment}
        res = requests.post(f"{BACKEND}/refine", json=payload)
        return res.json()["response"]

    def a3_quality(self, code):
        res = requests.post(f"{BACKEND}/quality", json={"code": code})
        return res.json()["response"]

    # -----------------------------
    # EXECUTION PIPELINE
    # -----------------------------
    def execute(self):
        current_code = self.chat_env.get("code")
        print("=== INITIAL CODE ===")
        print(current_code)
        previous_feedback = None

        format_attempt_count = 0
        quality_attempt_count = 0

        for round_id in range(self.max_rounds):

            print(f"\n================ ROUND {round_id + 1} ================")

            # -------------- A1 --------------
            comment = self.a1_comment(current_code, previous_feedback)
            self.chat_env.append_history("Reviewer", comment)
            #print("\n--- Reviewer Comments ---")
            #print(comment)
            self.chat_env.update("comments", comment)

            # -------------- A4 Format Judge --------------
            format_attempt_count += 1
            format_output = self.a4_format_judge(comment)
            #print("\n--- Format Judgment ---")
            #print(format_output)

            # parse decision
            raw = re.sub(
                r'"decision"\s*:\s*([A-Z]+)',
                r'"decision": "\1"',
                format_output
            )

            try:
                fj = json.loads(raw)
                fj_decision_raw = fj.get("decision", "").strip().upper()
                fj_feedback = fj.get("feedback", "").strip()
            except:
                fj_decision_raw = "REJECT"
                fj_feedback = format_output

            fj_accept = (fj_decision_raw == "ACCEPT")

            if not fj_accept:
                if format_attempt_count >= self.max_format_attempts:
                    fj_accept = True  # forced accept
                else:
                    # retry from Phase 1
                    previous_feedback = {
                        "source": "format",
                        "decision": 0,
                        "justification": fj_feedback,
                        "previous_comments": comment,
                        "previous_code": current_code
                    }
                    continue

            # -------------- A2 Refinement --------------
            proposed_code = self.a2_refine(current_code, comment)
            #print("\n--- Proposed Code ---")
            #print(proposed_code)
            self.chat_env.append_history("Developer", proposed_code)

            # -------------- A3 QE --------------
            quality_attempt_count += 1
            qe_output = self.a3_quality(proposed_code)
            #print("\n--- Quality Evaluation ---")
            #print(qe_output)

            try:
                q = json.loads(qe_output)
                qe_decision = int(q.get("decision", 0))
                qe_feedback = q.get("justification", "")
            except:
                qe_decision = 0 if "accept" in qe_output.lower() else 1
                qe_feedback = qe_output

            # ============= KEY LOGIC FIX =============
            if qe_decision == 0:
                # QE ACCEPT → finish immediately
                #print("\n🎉 FINAL: FORMAT & QUALITY ACCEPTED")
                current_code = proposed_code
                self.chat_env.update_code(proposed_code)
                print(proposed_code)
                return proposed_code

            # QE rejected
            if quality_attempt_count >= self.max_quality_attempts:
                # Force accept after limit
                #print("\n⚠ QUALITY LIMIT REACHED — forcing accept")
                #print("\n🎉 FINAL: FORMAT & QUALITY ACCEPTED")
                current_code = proposed_code
                self.chat_env.update_code(proposed_code)
                return proposed_code

            # Retry from Phase 1
            previous_feedback = {
                "source": "quality",
                "decision": 1,
                "justification": qe_feedback,
                "previous_comments": comment,
                "previous_code": current_code
            }
            
            format_attempt_count = 0
            continue

        # If we exit max_rounds without acceptance
        #print("\n⚠ MAX ROUNDS REACHED — forcing accept")
        #print("\n🎉 FINAL: FORMAT & QUALITY ACCEPTED")
        self.chat_env.update_code(proposed_code)
        print(proposed_code)
        return proposed_code

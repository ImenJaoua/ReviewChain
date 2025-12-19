# phase_backend.py
import json
import re
from chat_env import ChatEnv

from agents_local import (
    comment_generator,
    code_refiner,
    quality_estimator,
    # format_judge
)

class ReviewPhase:
    def __init__(self, chat_env: ChatEnv, max_rounds=20):
        self.chat_env = chat_env
        self.max_rounds = max_rounds
        self.max_format_attempts = 3
        self.max_quality_attempts = 6
    
    # -----------------------------
    # Direct agent functions (replace backend calls)
    # -----------------------------
    def a1_comment(self, code, feedback=None):
        comments = comment_generator(code)
        self.chat_env.update("comments", comments)
        self.chat_env.append_history("Reviewer", comments)
        print("\n💬 Reviewer:\n", comments)
        return comments
    

    def a2_refine(self, code, comment):
        refined_code = code_refiner(code, comment)
        self.chat_env.update_code(refined_code)
        self.chat_env.append_history("Developer", refined_code)
        print("\n🧑‍💻 Developer:\n", refined_code)
        return refined_code
    
    def a3_quality(self, code):
        quality_output = quality_estimator(code)
        print("\n🔍 Quality Estimator:\n", quality_output)
        return quality_output
    
    # def a4_format_judge(self, comment):
    #     """Judge comment format directly"""
    #     # TODO: Implement your A4 format judge logic here
    #     # This should return JSON with "decision" and "feedback"
    #     raise NotImplementedError("Implement A4 format judge logic")
    

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
            self.chat_env.update("comments", comment)
            
            # -------------- A4 Format Judge --------------
            # format_attempt_count += 1
            # format_output = self.a4_format_judge(comment)
            
            # # parse decision
            # raw = re.sub(
            #     r'"decision"\s*:\s*([A-Z]+)',
            #     r'"decision": "\1"',
            #     format_output
            # )
            # try:
            #     fj = json.loads(raw)
            #     fj_decision_raw = fj.get("decision", "").strip().upper()
            #     fj_feedback = fj.get("feedback", "").strip()
            # except:
            #     fj_decision_raw = "REJECT"
            #     fj_feedback = format_output
            
            # fj_accept = (fj_decision_raw == "ACCEPT")
            
            # if not fj_accept:
            #     if format_attempt_count >= self.max_format_attempts:
            #         fj_accept = True  # forced accept
            #     else:
            #         # retry from Phase 1
            #         previous_feedback = {
            #             "source": "format",
            #             "decision": 0,
            #             "justification": fj_feedback,
            #             "previous_comments": comment,
            #             "previous_code": current_code
            #         }
            #         continue
            
            # -------------- A2 Refinement --------------
            proposed_code = self.a2_refine(current_code, comment)
            self.chat_env.append_history("Developer", proposed_code)
            
            # -------------- A3 QE --------------
            quality_attempt_count += 1
            qe_output = self.a3_quality(proposed_code)
            
            try:
                q = json.loads(qe_output)
                qe_decision = int(q.get("decision", 0))
                qe_feedback = q.get("justification", "")
            except:
                qe_decision = 0 if "accept" in qe_output.lower() else 1
                qe_feedback = qe_output
            
            # ============= KEY LOGIC =============
            if qe_decision == 0:
                # QE ACCEPT → finish immediately
                current_code = proposed_code
                self.chat_env.update_code(proposed_code)
                print(proposed_code)
                return proposed_code
            
            # QE rejected
            if quality_attempt_count >= self.max_quality_attempts:
                # Force accept after limit
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
        self.chat_env.update_code(proposed_code)
        print(proposed_code)
        return proposed_code
# one_round_backend.py
import json
import requests
from chat_env import ChatEnv

BACKEND = "http://localhost:8000"

class ReviewPhase:
    def __init__(self, chat_env: ChatEnv):
        self.chat_env = chat_env

    # ---------- Backend wrappers ----------
    def a1_comment(self, code):
        res = requests.post(f"{BACKEND}/generate_comment", json={"code": code})
        return res.json()["response"]

    def a2_refine(self, code, comment):
        res = requests.post(f"{BACKEND}/refine",
                            json={"code": code, "comment": comment})
        return res.json()["response"]

    def a3_quality(self, code):
        res = requests.post(f"{BACKEND}/quality", json={"code": code})
        return res.json()["response"]

    # ---------- One-round pipeline ----------
    def execute(self):
        code = self.chat_env.get("code")

        # A1 COMMENT
        print("\n--- A1: Comment Generation ---")
        comment = self.a1_comment(code)
        print("A1 Comment:", comment)

        # A2 REFINEMENT
        print("\n--- A2: Refinement ---")
        refined = self.a2_refine(code, comment)
        print("A2 Refined Code:", refined)

        # A3 QUALITY
        print("\n--- A3: Quality Estimation ---")
        qe_output = self.a3_quality(refined)
        print("A3 Output:", qe_output)

        # Try to parse decision
        try:
            q = json.loads(qe_output)
            decision = int(q.get("decision", 0))
        except:
            decision = 0 if "accept" in qe_output.lower() else 1

        if decision == 1:
            print("⚠️ Quality rejected — but single round → keeping refined code")

        return refined.strip()

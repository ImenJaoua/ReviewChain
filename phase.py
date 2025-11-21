# phase.py
from chat_env import ChatEnv
from agents_local import comment_generator, code_refiner


class ReviewPhase:
    """
    One phase of collaboration between Reviewer (A1) and Developer (A2).
    Handles multiple review rounds until code passes tests or is approved.
    """

    def __init__(self, chat_env: ChatEnv, max_rounds=3):
        self.chat_env = chat_env
        self.max_rounds = max_rounds

    def execute(self):
        """Run iterative dialogue between A1 and A2."""
        code = self.chat_env.get("code")

        print(" Code : ",code)

        for round_id in range(self.max_rounds):
            print(f"\n=== ROUND {round_id + 1} ===")
            self.chat_env.next_iteration()

            # --- Step 1: Reviewer (A1)
            comments = comment_generator(code)
            self.chat_env.update("comments", comments)
            self.chat_env.append_history("Reviewer", comments)
            print("\n💬 Reviewer:\n", comments)

            # --- Step 2: Developer (A2)
            refined_code = code_refiner(code, comments)
            self.chat_env.update_code(refined_code)
            self.chat_env.append_history("Developer", refined_code)
            print("\n🧑‍💻 Developer:\n", refined_code)



        print("\n📄 Final Code:\n", self.chat_env.get_code())
        return self.chat_env.get_code()

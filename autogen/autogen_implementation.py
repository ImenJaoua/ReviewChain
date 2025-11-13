import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from autogen_agentchat.agents import AssistantAgent


from comment_prompt import (
    review_classification_system_prompt,
    review_classification_template,
)
from ref_prompt import (
    review_classification_system_prompt_ref,
    review_classification_template_ref,
)


# ============================================================
# 1. Local Model Client (compatible with autogen)
# ============================================================
def create_custom_model_client(model_name, max_tokens=512):
    """Local HuggingFace model wrapped for autogen"""
    class CustomModelClient:
        def __init__(self, model_name, max_tokens):
            self.model_name = model_name
            self.max_tokens = max_tokens

            self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype=torch.float16
            ).eval()

            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer
            )

        def create(self, params):
            """Generate using chat template"""
            messages = params.get("messages", [])
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            response = self.generator(
                prompt,
                max_new_tokens=self.max_tokens,
                return_full_text=False,
                do_sample=False
            )
            return response[0]["generated_text"]

    return CustomModelClient(model_name, max_tokens)


# ============================================================
# 2. Autogen Agent Setup
# ============================================================


def create_agents():
    """Create Comment Generator and Code Refiner agents (official way)."""
    comment_client = create_custom_model_client("trained_model_A1", max_tokens=512)
    refiner_client = create_custom_model_client(
        "deepseek-ai/deepseek-coder-6.7b-instruct", 
        max_tokens=512
    )

    # Agents reference registered models by name
    comment_agent = AssistantAgent(
        name="CommentGenerator",
        system_message=review_classification_system_prompt,
        model_client=comment_client,
    )

    refiner_agent = AssistantAgent(
        name="CodeRefiner",
        system_message=review_classification_system_prompt_ref,
        model_client=refiner_client,
    )

    return comment_agent, refiner_agent
# ============================================================
# 3. Two-Agent Code Review Loop
# ============================================================
def run_review_session(initial_code: str, old_code: str = "", num_rounds: int = 3):
    """Run iterative review-refine loop between two agents"""
    comment_agent, refiner_agent = create_agents()
    current_code = initial_code

    print("\n" + "="*70)
    print("Starting Autogen Code Review Session")
    print("="*70 + "\n")

    for round_num in range(num_rounds):
        print(f"\n🔁 ROUND {round_num + 1}/{num_rounds}")
        print("-" * 70)

        # Step 1: Comment Generator
        comment_prompt = review_classification_template.format(
            code_diff=current_code.strip()
        )
        comment_response = comment_agent.generate_reply(
            messages=[
                {"role": "system", "content": review_classification_system_prompt},
                {"role": "user", "content": comment_prompt}
            ]
        )
        review_comment = comment_response
        print(f"\n📝 Review Comment:\n{review_comment}\n")

        # Step 2: Code Refiner
        refiner_prompt = review_classification_template_ref.format(
            code_diff=current_code.strip(),
            review_comment=review_comment.strip(),
            old_file=old_code.strip() if old_code else ""
        )
        refiner_response = refiner_agent.generate_reply(
            messages=[
                {"role": "system", "content": review_classification_system_prompt_ref},
                {"role": "user", "content": refiner_prompt}
            ]
        )
        refined_code = refiner_response
        print(f"💻 Refined Code:\n{refined_code}\n")

        current_code = refined_code

    print("\n✅ REVIEW SESSION COMPLETE\n")
    return current_code


# ============================================================
# 4. Example Run
# ============================================================
if __name__ == "__main__":
    initial_code = """@@ -595,8 +595,10 @@ namespace Kratos
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

    old_code = """
            array_1d<double, 3> a = ZeroVector(3);
            a[0] = 2.0;
            array_1d<double, 3> b = ZeroVector(3);
            b[0] = 1.0;

            const array_1d<double, 3>  c = MathUtils<double>::CrossProduct(a, b);
            const array_1d<double, 3>  d = MathUtils<double>::UnitCrossProduct(a, b);
    """

    final_code = run_review_session(
        initial_code=initial_code,
        old_code=old_code,
        num_rounds=2
    )

    print("Final refined code:\n", final_code)

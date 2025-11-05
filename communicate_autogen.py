import torch
import asyncio
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.messages import TextMessage
from autogen_core.models import ChatCompletionClient, CreateResult, RequestUsage, LLMMessage

from comment_prompt import (
    review_classification_system_prompt,
    review_classification_template,
)
from ref_prompt import (
    review_classification_system_prompt_ref,
    review_classification_template_ref,
)


# ============================================================
# 1. Custom Model Client (Your Original Style, Adapted)
# ============================================================
def create_custom_model_client(model_name, max_tokens=512):
    """Local HuggingFace model wrapped for autogen v0.4.x"""
    
    class CustomModelClient(ChatCompletionClient):
        def __init__(self, model_name, max_tokens):
            self.model_name = model_name
            self.max_tokens = max_tokens

            print(f"Loading model: {model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
            
            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True
            ).eval()

            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer
            )
            print(f"✓ Model {model_name} loaded successfully")

        async def create(self, messages, **kwargs):
            """Generate using chat template (async for autogen v0.4.x)"""
            # Convert LLMMessage objects to dict format
            formatted_messages = []
            for msg in messages:
                # Handle different message formats
                if isinstance(msg, dict):
                    formatted_messages.append(msg)
                elif hasattr(msg, 'content'):
                    role = getattr(msg, 'role', 'user')
                    formatted_messages.append({
                        "role": role,
                        "content": msg.content
                    })
                else:
                    # Fallback: treat as string content
                    formatted_messages.append({
                        "role": "user",
                        "content": str(msg)
                    })
            
            # Debug: print what we're sending
            print(f"[DEBUG] Formatted messages: {formatted_messages}")
            
            # Apply chat template
            prompt = self.tokenizer.apply_chat_template(
                formatted_messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # Generate using pipeline
            response = self.generator(
                prompt,
                max_new_tokens=self.max_tokens,
                return_full_text=False,
                do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id
            )
            
            generated_text = response[0]["generated_text"]
            
            # Return in autogen v0.4.x format
            return CreateResult(
                content=generated_text,
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                finish_reason="stop",
                cached=False
            )
        
    return CustomModelClient(model_name, max_tokens)


# ============================================================
# 2. Autogen Agent Setup
# ============================================================
def create_agents():
    """Create Comment Generator and Code Refiner agents"""
    comment_client = create_custom_model_client("trained_model_A1", max_tokens=512)
    refiner_client = create_custom_model_client("deepseek-ai/deepseek-coder-6.7b-instruct", max_tokens=512)

    comment_agent = AssistantAgent(
        name="CommentGenerator",
        model_client=comment_client,
        system_message=review_classification_system_prompt,
        description="Analyzes code diffs and generates comments."
    )

    refiner_agent = AssistantAgent(
        name="CodeRefiner",
        model_client=refiner_client,
        system_message=review_classification_system_prompt_ref,
        description="Improves the code based on review comments."
    )

    return comment_agent, refiner_agent


# ============================================================
# 3. Two-Agent Code Review Loop
# ============================================================
async def run_review_session(initial_code: str, old_code: str = "", num_rounds: int = 3):
    """Run iterative review-refine loop between two agents"""
    comment_agent, refiner_agent = create_agents()
    current_code = initial_code

    print("\n" + "="*70)
    print("Starting Autogen Code Review Session")
    print("="*70 + "\n")

    for round_num in range(num_rounds):
        print(f"\n🔁 ROUND {round_num + 1}/{num_rounds}")
        print("-" * 70)

        try:
            # Step 1: Comment Generator
            comment_prompt = review_classification_template.format(
                code_diff=current_code.strip()
            )
            
            comment_response = await comment_agent.on_messages(
                [TextMessage(content=comment_prompt, source="user")],
                cancellation_token=None
            )
            
            review_comment = comment_response.chat_message.content
            print(f"\n📝 Review Comment:\n{review_comment}\n")

            # Step 2: Code Refiner (Agent 1 → Agent 2 communication)
            refiner_prompt = review_classification_template_ref.format(
                code_diff=current_code.strip(),
                review_comment=review_comment.strip(),  # ← OUTPUT from CommentGenerator
                old_file=old_code.strip() if old_code else ""
            )
            
            refiner_response = await refiner_agent.on_messages(
                [TextMessage(content=refiner_prompt, source="user")],
                cancellation_token=None
            )
            
            refined_code = refiner_response.chat_message.content
            print(f"💻 Refined Code:\n{refined_code}\n")

            # Update for next round
            current_code = refined_code
            
        except Exception as e:
            print(f"Error in round {round_num + 1}: {e}")
            import traceback
            traceback.print_exc()
            break

    print("\n✅ REVIEW SESSION COMPLETE\n")
    return current_code


# ============================================================
# 4. Alternative: Using RoundRobinGroupChat (for easy expansion)
# ============================================================
async def run_review_with_group_chat(
    initial_code: str,
    old_code: str = "",
    num_rounds: int = 3
):
    """Alternative approach using RoundRobinGroupChat for easier multi-agent expansion"""
    
    comment_agent, refiner_agent = create_agents()
    
    # Create a team with round-robin chat
    team = RoundRobinGroupChat([comment_agent, refiner_agent])
    
    # Initial message
    initial_prompt = review_classification_template.format(
        code_diff=initial_code.strip()
    )
    
    print("\n" + "="*70)
    print("Starting Group Chat Review Session")
    print("="*70 + "\n")
    
    # Run the team
    result = await team.run(task=initial_prompt)
    
    print("\n✅ GROUP CHAT SESSION COMPLETE\n")
    print(f"Final result:\n{result}\n")
    
    return result


# ============================================================
# 5. Example Run
# ============================================================
def main():
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

    final_code = asyncio.run(
        run_review_session(
            initial_code=initial_code,
            old_code=old_code,
            num_rounds=2
        )
    )

    print("\n" + "="*70)
    print("FINAL REFINED CODE:")
    print("="*70)
    print(final_code)


if __name__ == "__main__":
    main()
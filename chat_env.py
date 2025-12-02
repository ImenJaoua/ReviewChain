# chat_env.py
import os
import subprocess
import signal
import time
import json
from memory import Memory


class ChatEnvConfig:
    """
    Configuration for the ReviewChain environment.
    Similar to ChatDev's ChatEnvConfig.
    """

    def __init__(self,
                 clear_structure=False,
                 incremental_develop=False,
                 with_memory=True,
                 background_prompt="",
                 test_enabled=True):
        self.clear_structure = clear_structure
        self.incremental_develop = incremental_develop
        self.with_memory = with_memory
        self.background_prompt = background_prompt
        self.test_enabled = test_enabled

    def __str__(self):
        s = "ChatEnvConfig:\n"
        s += f"  with_memory: {self.with_memory}\n"
        s += f"  clear_structure: {self.clear_structure}\n"
        s += f"  incremental_develop: {self.incremental_develop}\n"
        s += f"  test_enabled: {self.test_enabled}\n"
        s += f"  background_prompt: {self.background_prompt}\n"
        return s


class ChatEnv:
    """
    Simplified environment for ReviewChain.

    Stores shared state between Reviewer (A1) and Developer (A2):
      - current code
      - latest comments
      - history of dialogue
      - optional persistent memory
    """

    def __init__(self, chat_env_config: ChatEnvConfig, initial_code: str = "", initial_file: str = ""):
        self.config = chat_env_config

        # Core shared state
        self.env_dict = {
            "code": initial_code,
            "comments": "",
            "history": [],
            "iteration": 0,
            "error_summary": "",
        }

        # Optional persistent memory
        self.memory = Memory() if self.config.with_memory else None
        if self.memory:
            self.memory.load()

    # ============================================================
    # 1. Environment access and updates
    # ============================================================

    def update(self, key: str, value):
        """Update or add an entry in the environment dictionary."""
        self.env_dict[key] = value

    def get(self, key: str):
        """Safely retrieve a value."""
        return self.env_dict.get(key, None)

    def reset(self, initial_code: str = ""):
        """Reset environment for a new review session."""
        self.env_dict = {
            "code": initial_code,
            "comments": "",
            "history": [],
            "iteration": 0,
            "error_summary": "",
        }

    # ============================================================
    # 2. Conversation management
    # ============================================================

    def append_history(self, role: str, message: str):
        """
        Append a message to the in-session history.
        If memory is active, persist it as well.
        """
        entry = {"role": role, "message": message.strip()}
        self.env_dict["history"].append(entry)

        if self.memory:
            self.memory.add(role, message)

    def print_history(self, limit: int = 5):
        """Print the last few conversation turns."""
        print("\n🧠 Conversation History (last {} turns):".format(limit))
        for h in self.env_dict["history"][-limit:]:
            role, msg = h["role"], h["message"]
            short_msg = msg[:120] + ("..." if len(msg) > 120 else "")
            print(f"  {role}: {short_msg}")

    def export_history(self, filename="conversation_log.json"):
        """Export full conversation history to JSON."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.env_dict["history"], f, indent=2)
        print(f"💾 Conversation saved to {filename}")

    # ============================================================
    # 3. Code management
    # ============================================================

    def update_code(self, new_code: str):
        """Update the main working code snippet."""
        self.env_dict["code"] = new_code

    def get_code(self) -> str:
        """Retrieve current code."""
        return self.env_dict["code"]


    # ============================================================
    # 5. Iteration control
    # ============================================================

    def next_iteration(self):
        """Increment the iteration counter."""
        self.env_dict["iteration"] += 1

    def get_iteration(self) -> int:
        """Get current iteration number."""
        return self.env_dict["iteration"]

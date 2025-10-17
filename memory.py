import os, json

class Memory:
    """
    Lightweight persistent memory for ReviewChain.
    Saves conversation logs to disk between sessions.
    """

    def __init__(self, directory="memory_store"):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
        self.filename = os.path.join(directory, "session_memory.json")
        self.data = []

    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = []

    def save(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def add(self, role, message):
        self.data.append({"role": role, "message": message})
        self.save()

    def get_recent(self, n=5):
        return self.data[-n:]

import pymongo
import ollama
from datetime import datetime

class TacticalAgent:
    def __init__(self):
        # Connect to your existing MongoDB
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client["JarvisTactical"]
        self.memory = self.db["doctrine"]
        self.model = "qwen2.5:7b" # Your optimized local model

    def store_doctrine(self, rule_text):
        """Saves a core principle that JARVIS must always follow."""
        self.memory.insert_one({
            "type": "doctrine",
            "content": rule_text,
            "timestamp": datetime.now()
        })

    def get_my_data(self):
        """Retrieves all your past logic and rules to stay loyal to YOUR style."""
        docs = self.memory.find({"type": "doctrine"})
        return "\n".join([d["content"] for d in docs])

    def evaluate_idea(self, idea):
        """The core tactical analysis engine."""
        my_doctrine = self.get_my_data()
        
        # This prompt forces JARVIS to be critical, not just helpful
        tactical_prompt = f"""
        USER DATA & DOCTRINE:
        {my_doctrine}

        YOU ARE JARVIS: A tactical advisor loyal ONLY to Rohith.
        ROHITH'S PROPOSAL: "{idea}"

        MISSION: Analyze this idea. Do not be a 'yes-man'. 
        If the idea is flawed, say so. If I insist, find the most efficient, 
        practical 'tactical' way to execute it that suits my specific style.

        OUTPUT FORMAT:
        1. [CRITICAL ANALYSIS]: Identify risks or inefficiencies.
        2. [TACTICAL EXECUTION]: The best practical step-by-step path.
        3. [LOYALTY CHECK]: How this aligns with your past goals.
        """

        response = ollama.chat(model=self.model, messages=[{'role': 'user', 'content': tactical_prompt}])
        return response['message']['content']
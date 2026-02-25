import mss
import ollama
from datetime import datetime
import os

class VisionEngine:
    def __init__(self, model="moondream"):
        self.model = model

    def capture_and_analyze(self, prompt="What is on my screen?"):
        # Unique filename to avoid collisions
        path = f"scan_{datetime.now().strftime('%H%M%S')}.png"
        
        try:
            with mss.mss() as sct:
                sct.shot(output=path)
            
            response = ollama.chat(model=self.model, messages=[{
                'role': 'user', 
                'content': prompt, 
                'images': [path]
            }])
            
            # Clean up the image after analysis
            if os.path.exists(path):
                os.remove(path)
                
            return response['message']['content']
        except Exception as e:
            return f"Vision Error: {str(e)}"
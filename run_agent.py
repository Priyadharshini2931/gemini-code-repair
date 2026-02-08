import os
import json
from datetime import datetime, UTC
import subprocess
import sys

# --- SDK Import with fallback ---
try:
    from google import genai
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-genai"])
    from google import genai

# --- Configuration ---
# The new SDK uses a Client object
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL_ID = "gemini-1.5-pro" 

LOG_FILE = "agent.log"

def log_event(event_type, content):
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "type": event_type,
        "content": content
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def write_file(path, content):
    log_event("tool_use", {"tool": "write_file", "path": path})
    full_path = os.path.join("/testbed", path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w') as f:
        f.write(content)
    return "File written successfully."

def main():
    task_id = os.environ.get("TASK_ID", "unknown")
    
    instruction = f"""
    You are an AI SWE-bench agent. Task ID: {task_id}
    Target: Improve ISBN import logic by using local staged records in openlibrary/core/imports.py
    Provide the full updated Python code for that file.
    """

    log_event("request", instruction)
    
    try:
        # New SDK syntax: client.models.generate_content
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=instruction
        )
        
        # Clean markdown code blocks if the model included them
        raw_text = response.text
        code_content = raw_text
        if "```python" in raw_text:
            code_content = raw_text.split("```python")[1].split("```")[0].strip()
        elif "```" in raw_text:
            code_content = raw_text.split("```")[1].split("```")[0].strip()

        log_event("response", raw_text)
        
        # Apply the fix to the testbed
        status = write_file("openlibrary/core/imports.py", code_content)
        print(f"Agent finished: {status}")

    except Exception as e:
        log_event("error", str(e))
        print(f"Error during generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

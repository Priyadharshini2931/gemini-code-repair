import os
import json
import datetime
import subprocess
import sys

# --- Self-Installation Guard ---
try:
    import google.generativeai as genai
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai"])
    import google.generativeai as genai

# --- Configuration ---
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-pro')

LOG_FILE = "agent.log"

def log_event(event_type, content):
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "type": event_type,
        "content": content
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def run_bash(command):
    log_event("tool_use", {"tool": "bash", "command": command})
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"

def read_file(path):
    log_event("tool_use", {"tool": "read_file", "path": path})
    try:
        with open(os.path.join("/testbed", path), 'r') as f:
            return f.read()
    except Exception as e:
        return str(e)

def write_file(path, content):
    log_event("tool_use", {"tool": "write_file", "path": path})
    full_path = os.path.join("/testbed", path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w') as f:
        f.write(content)
    return "File written successfully."

# --- Main Agent Logic ---
def main():
    task_id = os.environ.get("TASK_ID", "unknown")
    
    # Define the core instruction for Gemini
    instruction = f"""
    You are an AI SWE-bench agent. Your task is to fix a bug in the OpenLibrary repository.
    Task ID: {task_id}
    
    Target: Improve ISBN import logic by using local staged records.
    Primary File: openlibrary/core/imports.py
    
    1. Read the code.
    2. Propose a fix.
    3. Write the fix to the file.
    """

    log_event("request", instruction)
    
    # Simple one-shot repair for the hackathon
    # In a production agent, you would use loop-based tool calling
    response = model.generate_content(instruction + "\n\nProvide the full content for openlibrary/core/imports.py")
    
    # Extract code from Markdown if necessary
    code_content = response.text.replace("```python", "").replace("```", "").strip()
    
    log_event("response", response.text)
    
    # Apply the fix
    status = write_file("openlibrary/core/imports.py", code_content)
    print(f"Agent finished: {status}")

if __name__ == "__main__":
    main()

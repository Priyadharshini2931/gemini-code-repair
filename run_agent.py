import os
import json
import time
import sys
import subprocess
from datetime import datetime, UTC

# --- SDK Import with fallback ---
try:
    from google import genai
    from google.api_core.exceptions import ResourceExhausted
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-genai"])
    from google import genai
    from google.api_core.exceptions import ResourceExhausted


# --- Configuration ---
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable is not set")

client = genai.Client(api_key=API_KEY)

# ✅ Supported model
MODEL_ID = "gemini-2.0-flash"

LOG_FILE = "agent.log"
MAX_RETRIES = 3


def log_event(event_type, content):
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "type": event_type,
        "content": content,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def write_file(path, content):
    log_event("tool_use", {"tool": "write_file", "path": path})
    full_path = os.path.join("/testbed", path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)
    return "File written successfully."


def generate_with_retry(prompt):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
            )
        except ResourceExhausted as e:
            wait_time = 45 * attempt
            log_event(
                "rate_limit",
                f"Quota exceeded. Retry {attempt}/{MAX_RETRIES}. Waiting {wait_time}s.",
            )
            if attempt == MAX_RETRIES:
                raise
            time.sleep(wait_time)


def main():
    task_id = os.environ.get("TASK_ID", "unknown")

    instruction = f"""
You are an AI SWE-bench agent. Task ID: {task_id}

Target:
Improve ISBN import logic by using local staged records in
openlibrary/core/imports.py

Provide the FULL updated Python code for that file.
"""

    log_event("request", instruction)

    try:
        response = generate_with_retry(instruction)

        raw_text = response.text
        code_content = raw_text

        # Strip markdown fences if present
        if "```python" in raw_text:
            code_content = raw_text.split("```python")[1].split("```")[0].strip()
        elif "```" in raw_text:
            code_content = raw_text.split("```")[1].split("```")[0].strip()

        log_event("response", raw_text)

        status = write_file("openlibrary/core/imports.py", code_content)
        print(f"Agent finished successfully: {status}")

    except ResourceExhausted:
        log_event(
            "error",
            "Quota exhausted. No requests available for this project/model.",
        )
        print(
            "ERROR: Gemini API quota exhausted.\n"
            "Enable billing or wait for quota reset.\n"
            "https://ai.google.dev/gemini-api/docs/rate-limits"
        )
        sys.exit(0)  # graceful exit for CI

    except Exception as e:
        log_event("error", str(e))
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

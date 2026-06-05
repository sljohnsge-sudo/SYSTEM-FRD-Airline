import json

def read_logs():
    log_path = r"C:\Users\Sanka\.gemini\antigravity-ide\brain\057c4a5c-5fd8-493d-af23-6d99d9e202fd\.system_generated\logs\transcript.jsonl"
    with open(log_path, 'r', encoding='utf-8') as f:
        steps = [json.loads(line) for line in f]
    
    print("=== Chronological User Requests ===")
    for i, step in enumerate(steps):
        content = step.get("content", "")
        # Only check user inputs
        if step.get("source") == "USER_EXPLICIT" or step.get("type") == "USER_INPUT":
            # Extract request content
            req_content = ""
            if "<USER_REQUEST>" in content:
                req_content = content.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0].strip()
            else:
                req_content = content.strip()
            if req_content:
                print(f"Step {i}: {req_content}\n")

if __name__ == "__main__":
    read_logs()

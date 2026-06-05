import json

def read_changes():
    log_path = r"C:\Users\Sanka\.gemini\antigravity-ide\brain\057c4a5c-5fd8-493d-af23-6d99d9e202fd\.system_generated\logs\transcript.jsonl"
    with open(log_path, 'r', encoding='utf-8') as f:
        steps = [json.loads(line) for line in f]
    
    # Let's search for step 110 to 118
    for i in range(110, min(118, len(steps))):
        step = steps[i]
        print(f"\n=================== STEP {i} ({step.get('source')}, {step.get('type')}) ===================")
        tool_calls = step.get('tool_calls')
        if tool_calls:
            for tc in tool_calls:
                print(f"Tool call: {tc.get('name')}")
                # print args keys and snippet of replacement
                args = tc.get('args', {})
                for k, v in args.items():
                    if k in ['ReplacementContent', 'ReplacementChunks', 'CodeContent']:
                        print(f"  {k}: {str(v)[:500]}...")
                    else:
                        print(f"  {k}: {v}")

if __name__ == "__main__":
    read_changes()

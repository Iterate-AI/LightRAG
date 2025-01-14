import json
from collections import defaultdict

# Dictionary to store snippets by file path
file_snippets = defaultdict(list)

# Read the input JSONL file and group snippets by file path
with open('test_excalidraw.jsonl', 'r') as f:
    for line in f:
        try:
            data = json.loads(line)
            if 'context' in data and 'file_path' in data['context'] and 'snippet' in data['context']:
                file_path = data['context']['file_path']
                snippet = data['context']['snippet']
                file_snippets[file_path].append({
                    'filename': data['filename'],
                    'docstring': data['docstring'],
                    'snippet': snippet
                })
        except json.JSONDecodeError:
            continue

# Merge snippets for each file path and write to new JSONL
with open('merged_excalidraw.jsonl', 'w') as f:
    for file_path, snippets in file_snippets.items():
        # Sort snippets based on docstring sequence number if possible
        snippets.sort(key=lambda x: int(x['docstring'].split('-')[-1].strip()) if x['docstring'].split('-')[-1].strip().isdigit() else 0)
        
        # Merge snippets
        merged_snippet = ''.join(s['snippet'] for s in snippets)
        
        # Create merged record
        merged_record = {
            'filename': snippets[0]['filename'],
            'docstring': f"Merged content of {file_path}",
            'context': {
                'file_path': file_path,
                'snippet': merged_snippet
            }
        }
        
        # Write to output file
        f.write(json.dumps(merged_record) + '\n')

print("Merged JSONL file has been created as 'merged_excalidraw.jsonl'")

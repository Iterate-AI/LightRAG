import json
import numpy as np

# Open the destination.jsonl file for reading
with open('test_sinppet.jsonl', 'r') as jsonl_file:
    # Open code.txt in write mode
    with open('code_sinppet.txt', 'w') as code_file:
        # Keep track of snippets and their lengths
        snippets_with_lengths = []
        
        # Read each line from the JSONL file
        for line in jsonl_file:
            try:
                # Parse the JSON line
                data = json.loads(line)
                
                # Extract the snippet and filepath from the context if they exist
                if 'context' in data and 'snippet' in data['context'] and 'file_path' in data['context']:
                    snippet = data['context']['snippet']
                    filepath = data['context']['file_path']
                    
                    # Track snippet and its length 
                    snippets_with_lengths.append((snippet, len(snippet)))
                    
                    # Write the filepath and snippet to code.txt
                    code_file.write(f"``` filepath : {filepath}\n")
                    code_file.write(snippet)
                    code_file.write("\n```\n\n") # Add spacing between snippets
            except json.JSONDecodeError:
                # Skip invalid JSON lines
                continue
                
        # Calculate percentiles
        if snippets_with_lengths:
            lengths = [length for _, length in snippets_with_lengths]
            p99 = np.percentile(lengths, 99.99)
            max_len = max(lengths)
            
            print(f"Snippet length statistics:")
            print(f"99th percentile: {p99:.0f} chars")
            print(f"Maximum length: {max_len} chars")
            
            print("\nSnippets over 99th percentile:")
            for snippet, length in snippets_with_lengths:
                if length > p99:
                    print(f"\nLength: {length} chars")
                    # print("Snippet:")
                    # print(snippet)
                    print("-" * 80)

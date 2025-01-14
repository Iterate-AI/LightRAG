import json
import numpy as np
import tiktoken

MAX_TOKENS = 1024  # Setting a reasonable max token length

def get_token_length(text):
    encoding = tiktoken.encoding_for_model("gpt-4")
    return len(encoding.encode(text))

# Open the destination.jsonl file for reading
with open('merged_excalidraw.jsonl', 'r') as jsonl_file:
    # Open output jsonl file in write mode
    with open('code_excalidraw_batched.txt', 'w') as out_file:
        current_chunk = ""
        current_filepath = None
        
        # Read each line from the JSONL file
        for line in jsonl_file:
            try:
                # Parse the JSON line
                data = json.loads(line)
                
                # Extract the snippet and filepath from the context if they exist
                if 'context' in data and 'snippet' in data['context'] and 'file_path' in data['context']:
                    snippet = data['context']['snippet']
                    filepath = data['context']['file_path']
                    
                    formatted_snippet = f"``` filepath : {filepath}\n{snippet}\n```\n"
                    token_length = get_token_length(formatted_snippet)
                    
                    if token_length > MAX_TOKENS:
                        # If current snippet alone exceeds max tokens, split it
                        chunks = []
                        remaining = formatted_snippet
                        while remaining:
                            # Find a good split point around MAX_TOKENS
                            encoding = tiktoken.encoding_for_model("gpt-4")
                            tokens = encoding.encode(remaining)
                            if len(tokens) <= MAX_TOKENS:
                                chunks.append(remaining)
                                break
                            
                            # Split at MAX_TOKENS and find last newline
                            partial = encoding.decode(tokens[:MAX_TOKENS])
                            last_newline = partial.rfind('\n')
                            if last_newline == -1:
                                last_newline = len(partial)
                            
                            chunk = remaining[:last_newline]
                            if not chunk.startswith("``` filepath"):
                                chunk = f"``` filepath : {filepath}\n{chunk}"
                            if not chunk.endswith("```\n"):
                                chunk += "\n```\n"
                            
                            chunks.append(chunk)
                            remaining = remaining[last_newline:].strip()
                            if remaining and not remaining.startswith("``` filepath"):
                                remaining = f"``` filepath : {filepath}\n{remaining}"
                        
                        # Write each chunk as separate JSON lines
                        for chunk in chunks:
                            out_file.write(chunk)
                            out_file.write('\n----####^_^####----\n')
                            
                    else:
                        # If we have a current chunk, check if we can append
                        if current_chunk:
                            combined = current_chunk + formatted_snippet
                            if get_token_length(combined) <= MAX_TOKENS:
                                current_chunk = combined
                            else:
                                # Write current chunk directly instead of using json.dump
                                out_file.write(current_chunk)
                                out_file.write('\n----####^_^####----\n')
                                current_chunk = formatted_snippet
                        else:
                            current_chunk = formatted_snippet
                            
            except json.JSONDecodeError:
                # Skip invalid JSON lines
                continue
        
        # Write any remaining chunk
        if current_chunk:
            out_file.write(current_chunk)
            out_file.write('\n----####^_^####----\n')

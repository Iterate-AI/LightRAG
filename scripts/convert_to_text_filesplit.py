import json
import numpy as np
import tiktoken

MAX_TOKENS = 2048  # Setting max token length to 2048

def get_token_length(text):
    try:
        encoding = tiktoken.encoding_for_model("gpt-4")
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Error calculating token length: {e}")
        return 0

# Main processing block
try:
    # Open the destination.jsonl file for reading
    with open('merged_excalidraw.jsonl', 'r') as jsonl_file:
        # Open output jsonl file in write mode
        with open('code_excalidraw_split_by_file.txt', 'w') as out_file:
            count = 0
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
                            # Split into chunks of MAX_TOKENS size
                            lines = snippet.split('\n')
                            current_chunk = []
                            current_length = 0
                            
                            for line in lines:
                                line_formatted = line + '\n'
                                line_tokens = get_token_length(line_formatted)
                                
                                if line_tokens > MAX_TOKENS:
                                    # For long lines, concatenate them to fit within remaining space
                                    words = line.split()
                                    truncated_line = []
                                    running_length = current_length  # Initialize with current chunk's length
                                    
                                    for word in words:
                                        word_formatted = word + ' '
                                        word_tokens = get_token_length(word_formatted)
                                        
                                        if running_length + word_tokens <= MAX_TOKENS:
                                            truncated_line.append(word)
                                            running_length += word_tokens
                                        else:
                                            break
                                    
                                    # Use the truncated line instead of the full line
                                    line = ' '.join(truncated_line)
                                    line_formatted = line + '\n'
                                    line_tokens = get_token_length(line_formatted)
                                
                                if current_length + line_tokens <= MAX_TOKENS:
                                    current_chunk.append(line)
                                    current_length += line_tokens
                                else:
                                    # Write current chunk
                                    chunk_text = '\n'.join(current_chunk)
                                    chunk_formatted = f"``` filepath : {filepath}\n{chunk_text}\n```\n"
                                    out_file.write(chunk_formatted)
                                    out_file.write('\n----####^_^####----\n')
                                    print(f"Chunk size: {current_length} tokens")
                                    # Start new chunk
                                    current_chunk = [line]
                                    current_length = line_tokens
                                    
                            # Write final chunk if any remains
                            if current_chunk:
                                chunk_text = '\n'.join(current_chunk)
                                chunk_formatted = f"``` filepath : {filepath}\n{chunk_text}\n```\n"
                                out_file.write(chunk_formatted)
                                out_file.write('\n----####^_^####----\n')
                        else:
                            # If file is under MAX_TOKENS, write it as a single chunk
                            print(f"Chunk size: {token_length} tokens")
                            out_file.write(formatted_snippet)
                            out_file.write('\n----####^_^####----\n')
                            
                    count += 1
                except json.JSONDecodeError as e:
                    print(f"Skipping invalid JSON line: {e}")
                    continue
                except Exception as e:
                    print(f"Error processing line: {e}")
                    continue
            
            print(f"Processing complete. Processed {count} entries.")

except FileNotFoundError:
    print("Error: Input file 'merged_excalidraw.jsonl' not found.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    print("Script execution finished.")

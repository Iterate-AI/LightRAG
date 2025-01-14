import matplotlib.pyplot as plt
from tiktoken import get_encoding
import re
import numpy as np
def count_tokens(text):
    # Use GPT-4 tokenizer (cl100k_base)
    enc = get_encoding("cl100k_base")
    return len(enc.encode(text))

def get_chunk_sizes(filename):
    chunk_sizes = []
    current_chunk = []
    max_chunk = ""
    max_tokens = 0
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip() == '----####^_^####----':
                if current_chunk:
                    chunk_text = ''.join(current_chunk)
                    tokens = count_tokens(chunk_text)
                    chunk_sizes.append(tokens)
                    if tokens > max_tokens:
                        max_tokens = tokens
                        max_chunk = chunk_text
                current_chunk = []
            else:
                current_chunk.append(line)
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = ''.join(current_chunk)
            tokens = count_tokens(chunk_text)
            chunk_sizes.append(tokens)
            if tokens > max_tokens:
                max_chunk = chunk_text
    
    return chunk_sizes, max_chunk

def plot_distribution(filename):
    chunk_sizes, max_chunk = get_chunk_sizes(filename)
    
    plt.figure(figsize=(10, 6))
    plt.hist(chunk_sizes, bins=30, edgecolor='black')
    plt.title('Distribution of Chunk Sizes in Tokens')
    plt.xlabel('Number of Tokens')
    plt.ylabel('Frequency')
    plt.grid(True, alpha=0.3)
    
    # Add some statistics
    plt.axvline(x=np.mean(chunk_sizes), color='r', linestyle='--', label=f'Mean: {np.mean(chunk_sizes):.0f}')
    plt.axvline(x=np.median(chunk_sizes), color='g', linestyle='--', label=f'Median: {np.median(chunk_sizes):.0f}')
    
    plt.legend()
    plt.show()
    
    # Print some basic statistics
    print(f"Total chunks: {len(chunk_sizes)}")
    print(f"Mean size: {np.mean(chunk_sizes):.0f} tokens")
    print(f"Median size: {np.median(chunk_sizes):.0f} tokens")
    print(f"Max size: {max(chunk_sizes)} tokens")
    print(f"Min size: {min(chunk_sizes)} tokens")
    print("\nFirst 300 characters of largest chunk:")
    print(max_chunk[:300])

if __name__ == "__main__":
    plot_distribution("code_excalidraw_split_by_file.txt")


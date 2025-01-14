import json

def filter_messages(input_file='messages.jsonl', output_file='filtered_messages.jsonl'):
    """
    Filters messages from input JSONL file and writes matching ones to output JSONL file
    
    Args:
        input_file (str): Path to input JSONL file (default: messages.jsonl)
        output_file (str): Path to output JSONL file (default: filtered_messages.jsonl)
    """
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            message = json.loads(line)
            body = json.loads(message['body'])
            
            if body.get('git_repo_name') == 'excalidraw-dev':
                outfile.write(line)

if __name__ == '__main__':
    filter_messages()

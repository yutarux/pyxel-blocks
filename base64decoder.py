import base64

# Load the provided file and decode its contents from base64
file_path = 'base64encorded.txt'

with open(file_path, 'r') as file:
    encoded_content = file.read()

decoded_content = base64.b64decode(encoded_content).decode('utf-8', errors='ignore')

with open('base64encorded.txt', 'w') as file:
    file.write(decoded_content)

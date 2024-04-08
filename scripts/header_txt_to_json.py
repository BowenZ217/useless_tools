import json

# Path to the input text file
input_file_path = 'headers.txt'
# Path for the output JSON file
output_json_path = 'headers.json'

"""
Usage:
    - Open browser and login to the website.
    - Open developer tools (F12 or Ctrl+Shift+I).
    - Go to the Network tab.
    - Refresh the page.
    - Click on the first request (page URL) in the list.
    - Scroll down to the "Request Headers" section.
    - Select all text in the "Request Headers" section.
    - Paste the headers in the "headers.txt" file (with no empty lines).
    - See the example in headers.txt.
    - Run the script.
"""

# Initialize a dictionary to hold the header information
headers_dict = {}

# Read the input file and process each line
with open(input_file_path, 'r') as file:
    lines = file.readlines()
    key = None
    i = 0
    for line in lines:
        line = line.strip()
        if i == 0:
            key = line[:-1]
            i = 1
            continue
        else:
            headers_dict[key] = line
            i = 0
            key = None

# Write the dictionary to a JSON file
with open(output_json_path, 'w') as json_file:
    json.dump(headers_dict, json_file, indent=4)

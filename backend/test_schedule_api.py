
import requests
import datetime
import json

# Define the endpoint
url = "http://localhost:8000/schedule/"
start_date = datetime.datetime.now().date().strftime("%Y-%m-%d")

try:
    response = requests.get(url, params={"start_date": start_date})
    response.raise_for_status()
    data = response.json()
    
    print(f"--- API Response for Start Date: {start_date} ---")
    for block in data:
        # Check if block matches Tomorrow (Feb 15)
        print(f"Date: {block.get('date')}, Type: {block.get('type')}, ID: {block.get('id')}")

except Exception as e:
    print(f"Error fetching schedule: {e}")

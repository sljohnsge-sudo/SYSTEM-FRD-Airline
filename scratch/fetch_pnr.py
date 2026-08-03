import requests

# Create a session object
session = requests.Session()

# Step 1: Log in
login_url = "http://127.0.0.1:5000/login"
login_data = {
    "username": "premium_agent",
    "password": "agent123"
}
response = session.post(login_url, data=login_data)
print("Login status code:", response.status_code)

# Step 2: Fetch retrieve endpoint
retrieve_url = "http://127.0.0.1:5000/api/pnr/retrieve?pnr=PNR858098"
response2 = session.get(retrieve_url)
print("Retrieve PNR status code:", response2.status_code)
print("JSON response:")
print(response2.text)

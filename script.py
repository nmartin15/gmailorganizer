import os
import re
import json
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
USER_ID = 'me'
PARENT_LABEL_NAME = 'Subscriptions'
LABEL_DICT_FILE = 'label_dict.json'

def get_service():  # Gets Gmail service
    creds = None
    
    # Log the start of the function
    print("Starting get_service()...")
    
    if os.path.exists('token.json'):
        print("Found token.json, attempting to load credentials...")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if creds:
            print("Loaded credentials from token.json.")
        else:
            print("Failed to load credentials from token.json.")
            
    if not creds or not creds.valid:
        print("Credentials are either missing or not valid.")
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
            print("Credentials refreshed.")
        else:
            print("Getting new credentials...")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            print("New credentials obtained.")
        
        with open('token.json', 'w') as token:
            print("Saving credentials to token.json...")
            token.write(creds.to_json())
            print("Credentials saved.")
            
    # Log the end of the function
    print("Exiting get_service()...")
    
    return build('gmail', 'v1', credentials=creds)


def get_label_id(service, label_name): # Gets label ID for a given label name
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    for label in labels:
        if label['name'] == label_name:
            print(f"Found label ID for {label_name}: {label['id']}")
            return label['id']
    print(f"Label ID for {label_name} not found.")
    return None

def extract_email_from_string(s):  # Extracts email from string 
    """Extracts email from string s."""
    match = re.search(r'<(.+)>', s)
    return match.group(1) if match else s

def create_label(service, name, email):  # Creates a label for a given name and email
    print(f"Creating label for {name} and {email}...")
    domain = email.split('@')[1].split('.')[0]
    label_name = f"{PARENT_LABEL_NAME}/{name}/{domain}"
    new_label = {
        'name': label_name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show'
    }
    try:
        label_object = service.users().labels().create(userId='me', body=new_label).execute()
        label_id = label_object['id']
        print(f"Label {label_name} created with ID: {label_id}")
    except HttpError as error:
        if error.resp.status == 409:  # Conflict
            label_id = get_label_id(service, label_name)  # Get existing label ID
            print(f"Label {label_name} already exists with ID: {label_id}")
        else:
            print(f"An error occurred: {error}")
            label_id = None
    return label_id  # Returning label_id whether it's new or already exists



def label_callback(request_id, response, exception):
    print(f"Callback invoked for request ID: {request_id}")
    if exception is not None:
        print(f"An error occurred: {exception}")
    else:
        print(f"Message with ID {request_id} labeled successfully.")

def load_label_dict():
    if os.path.exists(LABEL_DICT_FILE):
        with open(LABEL_DICT_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_label_dict(label_dict):
    with open(LABEL_DICT_FILE, 'w') as f:
        json.dump(label_dict, f)

def label_incoming_emails(service, query=""):
    print("Labeling incoming emails...")
    page_token = None  # Initialize page_token for pagination
    while True:  # Keep looping to go through all pages
        results = service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
        messages = results.get('messages', [])
        
        if not messages:
            print("No messages found.")
            return

        print("Creating batch request...")
        batch = service.new_batch_http_request(callback=label_callback)
        
        for message in messages:  # Loop through messages
            print(f"Processing message ID: {message['id']}")
            msg_id = message['id']
            msg = service.users().messages().get(userId='me', id=msg_id).execute()
            sender_email = ''
            sender_name = ''
            for header in msg['payload']['headers']:
                if header['name'] == 'From':
                    sender_email = extract_email_from_string(header['value'])  # Extract sender email from header
                    sender_name = re.search(r'(.*)<', header['value']).group(1) if re.search(r'(.*)<', header['value']) else sender_email  # Extract sender name if possible

            label_id = label_dict.get(sender_email, None)  # Get label ID from label_dict

            if label_id is None:  # If label doesn't exist, create it
                label_id = create_label(service, sender_name.strip(), sender_email)
                if label_id:
                    label_dict[sender_email] = label_id  # Update the dictionary

            if label_id:  # If label exists, add it to batch request
                print(f"Adding label ID {label_id} to message ID {msg_id}")
                batch.add(service.users().messages().modify(
                    userId='me', 
                    id=msg_id, 
                    body={'addLabelIds': [label_id], 'removeLabelIds': ['INBOX']}
                ), request_id=msg_id)
        
        print("Executing batch request...")
        batch.execute()

        # Check for more pages
        page_token = results.get('nextPageToken')
        if not page_token:
            break


if __name__ == '__main__':  # Main function
    service = get_service()

    # Calculate date one year ago
    today = datetime.date.today()
    one_year_ago = today - datetime.timedelta(days=365)

    # Create query string
    query = f"after:{one_year_ago}"

    # Load label dictionary from file
    label_dict = load_label_dict()

    # Call label_incoming_emails() with query as a parameter
    label_incoming_emails(service, query)

    # Save the updated label_dict back to the file
    save_label_dict(label_dict)







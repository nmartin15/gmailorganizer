# Gmail Subscription Organizer

## Description
This project organizes your Gmail subscriptions into neatly labeled folders. It uses the Gmail API to scan your inbox for subscription emails, creates unique labels for each sender, and moves those emails into the appropriate labels.

## Features
- Automated labeling of subscription emails
- Sorts emails based on the sender's domain
- Uses OAuth2 for secure authentication

## Requirements
- Python 3.x
- Google API Python client library
- `credentials.json` file for Gmail API authentication

## Setup

### Clone the Repository:
```bash
git clone https://github.com/nmartin15/gmailorganizer.git

Install Dependencies:
pip install --upgrade google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2

Get Gmail API credentials:
Visit Google Cloud Console, create a project and enable Gmail API. Download the credentials.json file and place it in the project folder.

Run the Script:
python script.py

How it Works
The script will:

Authenticate using OAuth2
Scan your Gmail inbox for emails based on a set query
Create unique labels for each sender
Move emails to the appropriate label folders

License:
MIT License

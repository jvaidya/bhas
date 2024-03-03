import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
DRIVE_SERVICE = None
DOCS_SERVICE = None
CREDS = None
EXISTING_FILES = {}

def get_drive_service():
  global DRIVE_SERVICE
  if DRIVE_SERVICE is None:
    creds = get_creds()
    DRIVE_SERVICE = build("drive", "v3", credentials=creds)

  return DRIVE_SERVICE

def get_docs_service():
  global DOCS_SERVICE
  if DOCS_SERVICE is None:
    creds = get_creds()
    DOCS_SERVICE = build("docs", "v1", credentials=creds)

  return DOCS_SERVICE

def get_creds():
  global CREDS
  if CREDS is not None:
    return CREDS
  creds = None
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())
    CREDS = creds
    return CREDS

def delete_all_files():
    service = get_drive_service()
    fileList = service.files().list().execute()
    # delete files first
    for f in fileList['files']:
      if 'folder' not in f['mimeType']:
        service.files().delete(fileId=f['id']).execute()
        print(f"Deleted {f['name']}")
    # now delete folders
    for f in fileList['files']:
      if 'folder' in f['mimeType']:
        service.files().delete(fileId=f['id']).execute()
        print(f"Deleted {f['name']}")
    postList = service.files().list().execute()
    if len(postList['files']) == 0:
      print("Deleted all files")
    
if __name__ == '__main__':
    delete_all_files()
    
        

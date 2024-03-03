import os.path
import sys
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

def read_existing_files():
  global EXISTING_FILES
  service = get_drive_service()
  fileList = service.files().list().execute()
  for f in fileList['files']:
    EXISTING_FILES[f['name']] = f['id']
      
def share_file(file_id):
  """
  """

  try:
    # create drive api client
    service = get_drive_service()
    request_body = {
      'role': 'reader',
      'type': 'anyone'
    }

    response_permission = service.permissions().create(
      fileId=file_id,
      body=request_body
    ).execute()

    print(response_permission)


    # Print Sharing URL
    response_share_link = service.files().get(
      fileId=file_id,
      fields='webViewLink'
    ).execute()

    print(response_share_link)

    return response_share_link['webViewLink']
  except HttpError as error:
    print(f"An error occurred: {error}")
    return None

def upload_to_folder(folder_id, filePath):
  """Upload a file to the specified folder and prints file ID, folder ID
  Args: Id of the folder
  Returns: ID of the file uploaded

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  fileName = os.path.basename(filePath)
  global EXISTING_FILES
  if fileName in EXISTING_FILES:
    return EXISTING_FILES[fileName]
  
  try:
    # create drive api client
    service = get_drive_service()

    file_metadata = {"name": fileName, "parents": [folder_id]}
    media = MediaFileUpload(
        filePath, mimetype="image/jpeg", resumable=True
    )
    # pylint: disable=maybe-no-member
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )
    print(f'File ID: "{file.get("id")}".')
    return file.get("id")

  except HttpError as error:
    print(f"An error occurred: {error}")
    return None

def create_folder(folderName):
  """Create a folder and prints the folder ID
  Returns : Folder Id

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  global EXISTING_FILES
  if folderName in EXISTING_FILES:
    return EXISTING_FILES[folderName]
  
  try:
    # create drive api client
    service = get_drive_service()
    file_metadata = {
        "name": folderName,
        "mimeType": "application/vnd.google-apps.folder",
    }

    # pylint: disable=maybe-no-member
    file = service.files().create(body=file_metadata, fields="id").execute()
    print(f'Folder ID: "{file.get("id")}".')
    return file.get("id")

  except HttpError as error:
    print(f"An error occurred: {error}")
    return None

def create_composite_document(title, text, imageUri):

  try:
    # create drive api client
    service = get_docs_service()
    
    body = {
        'title': title
    }
    doc = service.documents() \
                 .create(body=body).execute()
    documentId = doc.get('documentId')
    print('Created document with title: {0} id: {1}'.format(doc.get('title'), documentId))

    requests = [
        {
            'insertText': {
                'location': {
                    'index': 1,
                },
                'text': text + "\n"
            }
        },
      {
        'insertInlineImage': {
            'location': {
                'index': 1,
            },
            'uri': imageUri
        }
      }      
    ]

    response = service.documents().batchUpdate(
        documentId=documentId, body={'requests': requests}).execute()

    insert_inline_image_response = response.get('replies')[1].get('insertInlineImage')
    print('Inserted image with object ID: {0}'.format(
        insert_inline_image_response.get('objectId')))
    return documentId
  except HttpError as error:
    print(f"An error occurred: {error}")
    return None
  
def move_file_to_folder(file_id, folder_id):
  """Move specified file to the specified folder.
  Args:
      file_id: Id of the file to move.
      folder_id: Id of the folder
  Print: An object containing the new parent folder and other meta data
  Returns : Parent Ids for the file

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """

  try:

    service = get_drive_service()
    
    # pylint: disable=maybe-no-member
    # Retrieve the existing parents to remove
    file = service.files().get(fileId=file_id, fields="parents").execute()
    previous_parents = ",".join(file.get("parents"))
    # Move the file to the new folder
    file = (
        service.files()
        .update(
            fileId=file_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields="id, parents",
        )
        .execute()
    )
    return file.get("parents")

  except HttpError as error:
    print(f"An error occurred: {error}")
    return None

def delete_file(fileId):
  try:
    service = get_drive_service()
    service.files().delete(fileId=fileId).execute()
  except HttpError as error:
    print(f"An error occurred: {error}")
  
def create_composite_files(bookDir):
  bookName = os.path.basename(bookDir)
  folderId = create_folder(bookName)
  jpgFiles = [f for f in os.listdir(bookDir) if f.endswith(".jpg")]
  for jpgFile in jpgFiles:

    # Upload jpeg file t drive
    fileId = upload_to_folder(folderId, os.path.join(bookDir, jpgFile))

    # Share the file
    share_file(fileId)

    baseName = jpgFile.split(".")[0]
    txtFile = baseName + ".txt"

    # Make sure the corresponding txt file exists
    if not os.path.exists(os.path.join(bookDir, txtFile)):
      print(f"{txtFile} does not exist, skipping")
      continue

    # Read txt file
    with open(os.path.join(bookDir, txtFile)) as f:
      text = f.read()

    pageUri = "https://drive.google.com/uc?id=" + fileId

    # Create composite document and inser text and Image into it
    docId = create_composite_document(baseName, text, pageUri)

    # Move the composite document to the folder
    move_file_to_folder(file_id=docId, folder_id=folderId)

    # Delete the jpeg file from drive
    delete_file(fileId)

if __name__ == "__main__":
  if len(sys.argv) == 1:
    print(f"Usage: {sys.argv[0]} <path to BookName directory with .jpg and .txt files>")
    sys.exit(1)

  # Read exisiting files created by this app so that we do not duplicate effort
  # Use cleanup.py to delete existing files if you wish to recreate them
  read_existing_files()

  bookDir = sys.argv[1]                           
  create_composite_files(bookDir)


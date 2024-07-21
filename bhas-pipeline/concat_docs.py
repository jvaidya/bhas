import os.path
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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
    allFiles = []
    fileList = service.files().list().execute()
    allFiles.extend(fileList['files'])    
    while ('nextPageToken' in fileList):
        fileList = service.files().list(pageToken=fileList['nextPageToken']).execute()
        allFiles.extend(fileList['files'])    
    for f in allFiles:
        EXISTING_FILES[f['name']] = f['id']


def create_concatenated_document(title, textlist):

    try:
        # create drive api client
        service = get_docs_service()

        body = {
            'title': title
        }
        doc = service.documents() \
                     .create(body=body).execute()
        documentId = doc.get('documentId')
        print('Created document with title: {0} id: {1}'.format(
            doc.get('title'), documentId))
        requests = []
        textlist.reverse()
        for text in textlist:
            requests.append(
                {
                    'insertText': {
                        'location': {
                            'index': 1,
                        },
                        'text': text + "XXX"
                    }
                })
        
        _ = service.documents().batchUpdate(
            documentId=documentId, body={'requests': requests}).execute()

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


def read_files(bookname, start, end):
    filenames = []
    for i in range(start, end + 1):
        filenames.append(f"{bookname}_page_{i}")
    textlist = []
    for fname in filenames:
        textlist.append(read_text(fname))
    return textlist

def read_text(fileName):
    fileId = EXISTING_FILES[fileName]
    docs_service = get_docs_service()
    doc = docs_service.documents().get(documentId=fileId).execute()
    doc_content = doc.get('body').get('content')
    return read_structural_elements(doc_content)

def read_paragraph_element(element):
    """Returns the text in the given ParagraphElement.

        Args:
            element: a ParagraphElement from a Google Doc.
    """
    text_run = element.get('textRun')
    if not text_run:
        return ''
    return text_run.get('content')


def read_structural_elements(elements):
    """Recurses through a list of Structural Elements to read a document's text where text may be
        in nested elements.

        Args:
            elements: a list of Structural Elements.
    """
    text = ''
    for value in elements:
        if 'paragraph' in value:
            elements = value.get('paragraph').get('elements')
            for elem in elements:
                text += read_paragraph_element(elem)
        elif 'table' in value:
            # The text in table cells are in nested Structural Elements and tables may be
            # nested.
            table = value.get('table')
            for row in table.get('tableRows'):
                cells = row.get('tableCells')
                for cell in cells:
                    text += read_structural_elements(cell.get('content'))
        elif 'tableOfContents' in value:
            # The text in the TOC is also in a Structural Element.
            toc = value.get('tableOfContents')
            text += read_structural_elements(toc.get('content'))
    return text

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(
            f"Usage: {sys.argv[0]} BookName StartPage EndPage")
        sys.exit(1)

    bookName = sys.argv[1]
    startPage = sys.argv[2]
    endPage = sys.argv[3]
    
    # Read exisiting files created by this app so that we have fileId values
    read_existing_files()

    # Read text from specified files
    textlist = read_files(bookName, int(startPage), int(endPage))

    # Write the text into a new concatenated document
    docId = create_concatenated_document(f"{bookName}_pages_{startPage}_{endPage}", textlist)

    # Move the file to "bookName" folder if exists
    if bookName in EXISTING_FILES:
        folderId = EXISTING_FILES[bookName]
        move_file_to_folder(file_id=docId, folder_id=folderId)

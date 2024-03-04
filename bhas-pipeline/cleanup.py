import os
import os.path
import argparse
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
DRIVE_SERVICE = None
DOCS_SERVICE = None
CREDS = None
EXISTING_FILES = {}
FULL_PATHS = {}

# We are outputting a dot without newline for every file read.
# This unbuffers that output
os.environ['PYTHONUNBUFFERED'] = 1

def define_args():
    parser = argparse.ArgumentParser(
        description="List or Delete files in Drive that match the pattern")
    parser.add_argument(
        '--pattern',
        dest="pattern",
        default="all",
        help="Pattern to match file/folder names, default all files")
    parser.add_argument(
        '--mode',
        default="list",
        choices=["list", "delete"],
        help="Mode can be list or delete, default list.")    
    return parser

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


def act_on_files(pattern, mode):
    service = get_drive_service()    
    # act on only files first
    for fId in EXISTING_FILES.keys():
        if pattern != "all" and pattern not in FULL_PATHS[fId]:
            continue        
        if "/" not in FULL_PATHS[fId]:
            continue
        if mode == "delete":
            service.files().delete(fileId=fId).execute()
            print(f"Deleted {FULL_PATHS[fId]}")
        else:
            print(f"Did not delete {FULL_PATHS[fId]}")
    # now act on folders
    for fId in EXISTING_FILES.keys():
        if pattern != "all" and pattern not in FULL_PATHS[fId]:
            continue        
        if "/" in FULL_PATHS[fId]:
            continue
        if mode == "delete":
            service.files().delete(fileId=fId).execute()
            print(f"Deleted {FULL_PATHS[fId]}")
        else:
            print(f"Did not delete {FULL_PATHS[fId]}")

def get_name_from_id(fileId):
    if fileID not in EXISTING_FILES:
        try:
            rFile = service.files().get(fileId=fileId, fields="name").execute()
            EXISTING_FILES[fileId] = rFile.get("name")
        except Exception as e:
            EXISTING_FILES[fileId] = f"ID({fileId})"

    return EXISTING_FILES[fileId]

def get_full_path(fileId, pathString):
    service = get_drive_service()
    try:
        rFile = service.files().get(fileId=fileId, fields="parents, name").execute()
        if pathString:
            pathString = rFile.get("name") + "/" + pathString
        else:
            pathString = rFile.get("name")
    except Exception as e:
        return pathString
    for pId in rFile.get("parents"):
        return get_full_path(pId, pathString)
            
def read_all_files():
    service = get_drive_service()
    allFiles = []
    fileList = service.files().list().execute()
    allFiles.extend(fileList['files'])    
    while ('nextPageToken' in fileList):
        fileList = service.files().list(pageToken=fileList['nextPageToken']).execute()
        allFiles.extend(fileList['files'])    
    print("Reading files ", end="")
    for f in allFiles:
        EXISTING_FILES[f['id']] = f['name']
        FULL_PATHS[f['id']] = get_full_path(f['id'],"")
        #print(f"Read {FULL_PATHS[f['id']]}")
        print(".", end="")
    print(".")

args = define_args().parse_args()
read_all_files()
act_on_files(args.pattern, args.mode)

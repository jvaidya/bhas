import sys
import io
import time
import os
import pathlib
from google.cloud import vision


def jpgFileToTextFile(client, jpgFile, textFile):

    # if jpgFile does not exist, return without doing anything
    if not os.path.exists(jpgFile):
        print(f"{jpgFile} does not exist, skipping")
        return 0

    start_time = time.time()

    # Read image file
    with io.open(jpgFile, 'rb') as image_file:
        content = image_file.read()

    # Perform text detection by doing API call
    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    # If API call retuned error, print error and return
    if response.error.message:
        print(f"{jpgFile} could not be processed:", response.error.message)
        return 0

    # Write text in textFile
    with open(textFile, "w", encoding='utf-8') as f:
        f.write(response.full_text_annotation.text)

    # return elapsed time in milliseconds
    return int((time.time() - start_time) * 1000)


if len(sys.argv) == 1:
    print(f"Usage: {sys.argv[0]} <list of jpeg files or *.jpg for all>")
    sys.exit(1)

jpeg_files = sys.argv[1:]
client = vision.ImageAnnotatorClient()
for jpgFile in jpeg_files:
    textFile = jpgFile.split(".")[0] + ".txt"
    elapsed = jpgFileToTextFile(client, jpgFile, textFile)
    if elapsed:
        print(f"{jpgFile} -> {textFile} ({elapsed} ms)")

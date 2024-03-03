import sys
import time
import os

from pdf2image import convert_from_path, convert_from_bytes

START_PAGE = 122

def getOutFileName(base_name, page):
  sub = False
  if page < 6:
    return "{}_start_{}.jpg".format(base_name, page)
  else:
    if page < 42:
      return "{}_page_{}.jpg".format(base_name, page - 5)
    else:
      return "{}_page_{}.jpg".format(base_name, page)
  
def splitPDF(fileName):
  base_name = os.path.basename(fileName).split(".")[0]
  try:
    images = convert_from_path(fileName)
  except Exception as e:
    print(f"Failed to split {fileName}", repr(e))
    return 0
  page = START_PAGE - 1
  for image in images:
    rotated = image.rotate(270, expand=1)
    p1 = rotated.crop((0, 0, rotated.width/2, rotated.height))
    p2 = rotated.crop((rotated.width/2, 0, rotated.width, rotated.height))    
    page = page + 1
    outFile = getOutFileName(base_name, page)
    p1.save(outFile, 'JPEG')
    page = page + 1
    outFile = getOutFileName(base_name, page)    
    p2.save(outFile, 'JPEG')

    
  return page

if len(sys.argv) == 1:
    print(f"Usage: {sys.argv[0]} <list of pdf files or *.pdf for all>")
    sys.exit(1)
    
pdfFiles = sys.argv[1:]

for pdfFile in pdfFiles:
  startTime = time.time()
  numPages = splitPDF(pdfFile)
  elapsed = int(time.time() - startTime)
  print(f"Split {pdfFile} into {numPages} pages in {elapsed} seconds")


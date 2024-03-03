import sys
import time
import os
import argparse

from pdf2image import convert_from_path


def define_args():
    epilog = '''
Examples:

python3 {progname} --first-actual-page 5 --bookname Sthalantar SthalantarCoverTo40-41.jpg

python3 {progname} --first-actual-page 1 --first-page-number 42 --bookname Sthalantar Sthalantar42-43To80-81.pdf

python3 {progname} --first-actual-page 1 --first-page-number 122 --last-actual-page 144 --bookname Sthalantar Sthalantar122-123ToBackCover.pdf
'''.format(progname=sys.argv[0])
    parser = argparse.ArgumentParser(
        description="Extract jpeg files, one per page from a pdf file.",
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        'pdfFile',
        help="pdf file to process")
    parser.add_argument(
        '--first-actual-page',
        dest='firstActualPage', type=int, default=1,
        help="Useful if at the beginning of the book, there are pages that are not book text.")
    parser.add_argument(
        '--first-page-number',
        dest='firstPageNumber', type=int, default=1,
        help="Useful if a book is split into multiple pdf files. If the first page number is 43, use that value")
    parser.add_argument(
        '--last-actual-page',
        dest='lastActualPage', type=int,
        help="Useful if at the end of the book, there are pages that are not book text.")
    parser.add_argument(
        '-v', '--verbose', dest='verbose', type=bool)
    parser.add_argument(
        '--bookname', dest='bookName',
        help="Used for prefixing each output file. Required.", required=True)
    return parser


def getOutFileName(base_name, page):
    if args.firstActualPage > 1:
        if page < args.firstActualPage + 1:
            return f"{base_name}_BEGIN_{page}.jpg"
        else:
            return f"{base_name}_page_{page - args.firstActualPage}.jpg"
    if args.lastActualPage is not None:
        if page > args.lastActualPage:
            return f"{base_name}_END_{page - args.lastActualPage}.jpg"
    # default case
    return f"{base_name}_page_{page}.jpg"


def splitPDFTest(fileName):
    base_name = args.bookName
    try:
        images = range(1, 14)
    except Exception as e:
        print(f"Failed to split {fileName}", repr(e))
        return 0
    page = args.firstPageNumber - 1
    for image in images:
        page = page + 1
        outFile = getOutFileName(base_name, page)
        print(outFile)
        page = page + 1
        outFile = getOutFileName(base_name, page)
        print(outFile)

    return page - (args.firstPageNumber - 1)


def splitPDF(fileName):
    base_name = os.path.basename(fileName).split(".")[0]
    try:
        images = convert_from_path(fileName)
    except Exception as e:
        print(f"Failed to split {fileName}", repr(e))
        return 0
    page = args.firstPageNumber - 1
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

        return page - (args.firstPageNumber - 1)


def process_pdf(pdfFile):
    startTime = time.time()
    numPages = splitPDF(pdfFile)
    elapsed = int(time.time() - startTime)
    print(f"Split {pdfFile} into {numPages} pages in {elapsed} seconds")


args = define_args().parse_args()

if args.verbose:
    print(f"pdfFile = {args.pdfFile}")
    print(f"bookName = {args.bookName}")
    print(f"firstActualPage = {args.firstActualPage}")
    print(f"firstPageNumber = {args.firstPageNumber}")
    print(f"lastActualPage = {args.lastActualPage}")

process_pdf(args.pdfFile)

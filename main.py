from curses import wrapper
import argparse
import textwrap
# import PyPDF2 as pypdf
import pdftotext
import re
import sys
import time
sys.setrecursionlimit(1000000)

parser = argparse.ArgumentParser()
parser.add_argument("file", help="File to be read")
parser.add_argument("--page", help="Reader starting page number", type=int)
args = parser.parse_args()

if args.page:
    pagecounter = args.page+1
else:
    # Load previous state or simply go to the first page.
    pagecounter = 1

# f = open(args.file, "rb")
# textfile = pypdf.PdfFileReader(f)
with open(args.file, "rb") as f:
    textfile = pdftotext.PDF(f)
linecounter = 0  # load previous state or go 0


def wrap(text, width):
    paras = text.splitlines()
    out = [j for i in paras for j in textwrap.wrap(i, width=width)]
    return out


def get_lines(pagecounter):
    # x = textfile.getPage(pagecounter)
    text = textfile[pagecounter].replace("-\n", "")
    # text = str(x.extract_text()).replace("-\n", "")
    text = text.replace("\n", " ").replace("  ", " ")
    punctuation = re.compile(r"([^\d+])(\.|!|\?|;|\n|。|！|？|；|…|　|!|؟|؛)+")
    lines = []
    lines = punctuation.sub(r"\1\2<pad>", text)
    lines = [line.strip() for line in lines.split("<pad>") if line.strip()]
    # lines = re.findall(".*?[!?.]+(?=$|\s)", text)

    return lines


def main(stdscr, textfile, pagecounter, linecounter):
    lines = get_lines(pagecounter)

    rows, cols = stdscr.getmaxyx()
    stdscr.clear()
    pdf = textfile
    out = wrap(lines[linecounter], int(cols/3))
    cursor = 0
    slow_print = False

    if slow_print:
        for i in out:
            sentence = ""
            words = i.split(" ")
            for word in words:
                sentence += " " + word
                stdscr.refresh()
                stdscr.addstr(int(rows/2)-int(len(out)/2)+cursor, int(cols/3), sentence)
                stdscr.addstr(rows-2, 0, f"Line {linecounter} on page {pagecounter+1}/{len(textfile)}")
                time.sleep(0.1)

            cursor += 1
    else:
        for i in out:
            stdscr.addstr(int(rows/2)-int(len(out)/2)+cursor,
                          int(cols/3), i)
            cursor += 1

    stdscr.addstr(rows-2, 0, f"Line {linecounter} on page {pagecounter+1}/{len(textfile)}")
    key = stdscr.getch()

    if key in (110, 106, 10, 261, 258, 32):
        # n, j, enter, down-arrow, right-arrow, spacebar
        if linecounter < len(lines)-1:
            linecounter += 1
            main(stdscr, pdf, pagecounter, linecounter)
        else:
            # Go to the next page

            # if pagecounter < len(pdf):
            #     stdscr.addstr("bigger than pdf")
            #     # Needs testing
            #     main(stdscr, pdf, pagecounter, linecounter)
            #     return

            try:
                pagecounter += 1
                linecounter = 0
                main(stdscr, pdf, pagecounter, linecounter)
            except Exception:
                pagecounter -= 1
                linecounter = len(lines)-1
                main(stdscr, pdf, pagecounter, linecounter)

    elif key in (98, 107, 263, 260, 259):
        # b, k, backspace, left-arrow, up-arrow

        if linecounter > 0:
            linecounter -= 1
            main(stdscr, pdf, pagecounter, linecounter)
        elif pagecounter <= 0:
            try:
                pagecounter -= 1
                lines = get_lines(pagecounter)
                linecounter = len(lines)-1
                main(stdscr, pdf, pagecounter, linecounter)
            except Exception:
                pagecounter += 1
                linecounter = 0
                lines = get_lines(pagecounter)
                main(stdscr, pdf, pagecounter, linecounter)
        else:
            main(stdscr, pdf, pagecounter, linecounter)

    elif key == 104:
        try:
            pagecounter += 1
            linecounter = 0
            main(stdscr, pdf, pagecounter, linecounter)
        except Exception:
            pagecounter -= 1
            linecounter = 0
            main(stdscr, pdf, pagecounter, linecounter)

    elif key == 108:
        try:
            pagecounter -= 1
            linecounter = 0
            main(stdscr, pdf, pagecounter, linecounter)
        except Exception:
            pagecounter += 1
            main(stdscr, pdf, pagecounter, linecounter)

    elif key == 113:
        return

    else:
        if key == 103:
            keys = []

            def getkey():
                return stdscr.getkey()

            while True:
                key = getkey()
                stdscr.addstr(key)

                if key == "g":
                    break
                else:
                    keys.append(key)

            try:
                pagecounter = int("".join(keys))-1
            except Exception:
                pass

            try:
                linecounter = 0
                main(stdscr, pdf, pagecounter, linecounter)
            except Exception:
                pagecounter -= 1
                main(stdscr, pdf, pagecounter, linecounter)

        else:
            main(stdscr, textfile, pagecounter, linecounter)


wrapper(main, textfile, pagecounter, linecounter)

import curses
from curses import wrapper
import argparse
import textwrap
import sys
import json


def wrap(text, width):
    paras = text.splitlines()
    out = [j for i in paras for j in textwrap.wrap(i, width=width)]
    return out


def parse_html_string(s):
    from lxml import html

    utf8_parser = html.HTMLParser(encoding='utf-8')
    html_tree = html.document_fromstring(s, parser=utf8_parser)

    return html_tree


def get_headers(elem):
    for n in range(1, 7):
        headers = elem.xpath('./h{}'.format(n))

        if len(headers) > 0:
            text = headers[0].text_content().strip()
            if len(text) > 0:
                return text
    return None


def get_pages(item):
    body = parse_html_string(item.get_body_content())
    pages = []

    for elem in body.iter():
        if elem.get('id') is None:
            _text = None
            chapter = item.get_name()[:-5].replace("chapter", "Chapter ")

            if elem.text is not None:
                _text = elem.text

            if _text is None:
                _text = elem.get('aria-label')

            if _text is None:
                _text = get_headers(elem)

            pages.append((chapter, elem.get('id'), _text or elem.get('id')))

    return pages


def get_pages_for_items(items):
    pages_from_docs = [get_pages(item) for item in items]

    return [item for pages in pages_from_docs for item in pages]


def make_chapters(pages):
    chapters = {}
    for i in pages:

        if i[2] is not None:
            if i[0] in chapters and i[2]:
                chapters[i[0]] += i[2]
            else:
                chapters[i[0]] = i[2]

    for i in chapters.keys():
        chapters[i] = chapters[i].replace("\n", " ")

    return chapters


def show_index(stdscr, chapters):
    def print_menu(stdscr, selected_row_idx, chapters):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        stdscr.addstr((h-len(chapters))//2-1,
                      w//2-len("Chapter Selection:")//2, "Chapter Selection:")
        for idx, row in enumerate(chapters):
            x = w//2 - len(row)//2
            y = h//2 - len(chapters)//2 + idx
            if idx == selected_row_idx:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, row)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, row)
        stdscr.refresh()

    def print_center(stdscr, text):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        x = w//2 - len(text)//2
        y = h//2
        stdscr.addstr(y, x, text)
        stdscr.refresh()

    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    current_row = 0

    print_menu(stdscr, current_row, chapters)
    h, w = stdscr.getmaxyx()

    while 1:
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(chapters)-1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            return current_row
            if current_row == len(chapters)-1:
                break

        print_menu(stdscr, current_row, chapters)


def main(stdscr, filetype, chapters, chapter, linecounter=0):
    def get_document():
        if filetype == "pdf":
            from pdf_utils import PDF
            document = PDF(chapters, linecounter, chapter)
        elif filetype == "epub":
            from epub_utils import EPUB
            document = EPUB(chapters, linecounter, chapter)

        return document

    global slow_print, print_speed
    document = get_document()
    rows, cols = stdscr.getmaxyx()
    stdscr.clear()
    curses.curs_set(0)  # disable cursor blinking
    lines = document.get_lines()
    out = wrap(lines[linecounter], int(cols/3))
    cursor = 0
    stdscr.addstr(rows-2, 0, document.get_progress())

    if slow_print:
        import time
        for i in out:
            sentence = ""
            words = i.split(" ")
            for word in words:
                sentence += " " + word
                stdscr.refresh()
                stdscr.addstr(int(rows/2)-int(len(out)/2)+cursor,
                              int(cols/3), sentence)
                time.sleep(print_speed)
                stdscr.addstr(1, 1, str(print_speed))

            cursor += 1
    else:
        for i in out:
            stdscr.addstr(int(rows/2)-int(len(out)/2)+cursor,
                          int(cols/3), i)
            cursor += 1

    stdscr.addstr(rows-1, 0, "")  # readjust cursor position
    key = stdscr.getch()

    if key in (110, 106, 10, 261, 258, 32):
        # n, j, enter, down-arrow, right-arrow, spacebar
        if linecounter < len(lines)-1:
            linecounter += 1
            main(stdscr, filetype, chapters, chapter, linecounter)
        else:
            # Go to the next page
            try:
                chapter += 1
                linecounter = 0
                main(stdscr, filetype, chapters, chapter, linecounter)
            except Exception:
                chapter -= 1
                linecounter = len(lines)-1
                main(stdscr, filetype, chapters, chapter, linecounter)

    elif key in (98, 107, 263, 260, 259):
        # b, k, backspace, left-arrow, up-arrow

        if linecounter > 0:
            linecounter -= 1
            main(stdscr, filetype, chapters, chapter, linecounter)

        elif linecounter <= 0:
            if chapter > 0:
                chapter -= 1
                document = get_document()
                lines = document.get_lines()
                linecounter = len(lines)-1

            main(stdscr, filetype, chapters, chapter, linecounter)

        else:
            main(stdscr, filetype, chapters, chapter, linecounter)

    elif key == 104:
        try:
            chapter += 1
            linecounter = 0
            main(stdscr, filetype, chapters, chapter, linecounter)
        except Exception:
            chapter -= 1
            linecounter = 0
            main(stdscr, filetype, chapters, chapter, linecounter)

    elif key == 108:
        if chapter > 0:
            chapter -= 1
            linecounter = 0

        main(stdscr, filetype, chapters, chapter, linecounter)

    elif key == 9:
        if filetype == "epub":
            chapter = show_index(stdscr, chapters)

        main(stdscr, filetype, chapters, chapter)

    elif key == 115:
        if slow_print:
            slow_print = False
        else:
            slow_print = True

        main(stdscr, filetype, chapters, chapter, linecounter)

    elif key == 122:
        print_speed += 0.05

        main(stdscr, filetype, chapters, chapter, linecounter)

    elif key == 120:
        if print_speed >= 0.05:
            print_speed -= 0.05

        main(stdscr, filetype, chapters, chapter, linecounter)

    elif key == 113:
        global cpt, lct
        lct = linecounter
        cpt = chapter
        return

    else:
        if key == 103:
            keys = []

            def getkey():
                return stdscr.getkey()

            curses.curs_set(1)
            stdscr.addstr(rows-1, 0, "Go to: ")

            while True:
                key = getkey()
                stdscr.addstr(key)

                if key == "g":
                    curses.curs_set(0)
                    break
                else:
                    keys.append(key)

            try:
                target = int("".join(keys))
            except Exception:
                main(stdscr, filetype, chapters, chapter, linecounter)

            if filetype == "pdf":
                chapter = target - 1
                try:
                    linecounter = 0
                    main(stdscr, filetype, chapters, chapter, linecounter)
                except Exception:
                    chapter -= 1
                    main(stdscr, filetype, chapters, chapter, linecounter)

            elif filetype == "epub" and 0 <= target < 100:
                if target < 99:
                    chapter = target + 1
                else:
                    chapter = target

                linecounter, chapter = document.jump_to(chapter)
                main(stdscr, filetype, chapters, chapter, linecounter)

            else:
                main(stdscr, filetype, chapters, chapter, linecounter)

        else:
            main(stdscr, filetype, chapters, chapter, linecounter)


if __name__ == "__main__":
    sys.setrecursionlimit(1000000)
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="File to be read")
    parser.add_argument("--page", help="Page for PDF.", type=int)
    parser.add_argument("--chapter", help="Chapter for EPUB.")
    args = parser.parse_args()

    filename = args.file
    filetype = filename.split(".")[1]
    global slow_print, printing_speed
    slow_print = False
    print_speed = 0.1

    try:
        with open("dr-state.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    if filetype == "epub":
        import ebooklib
        from ebooklib import epub

        book = epub.read_epub(filename)
        items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
        pages = get_pages_for_items(items)
        chapters = make_chapters(pages)
        chapter = args.chapter

        if args.chapter:
            chapter = int(args.chapter) - 1
            linecounter = 0
        elif filename in data:
            chapter = data[filename]["chapter"]
            linecounter = data[filename]["linecounter"]
            slow_print = data[filename]["slow_print"]
            print_speed = data[filename]["print_speed"]
        else:
            chapter = 0
            linecounter = 0

        wrapper(main, filetype, chapters, chapter, linecounter)

    elif filetype == "pdf":
        import pdftotext

        with open(args.file, "rb") as f:
            textfile = pdftotext.PDF(f)

        if args.page:
            pagecounter = args.page + 1
            linecounter = 0
        elif filename in data:
            pagecounter = data[filename]["chapter"]
            linecounter = data[filename]["linecounter"]
            slow_print = data[filename]["slow_print"]
            printing_speed = data[filename]["printing_speed"]
        else:
            pagecounter = 1
            linecounter = 0

        wrapper(main, filetype, textfile, pagecounter, linecounter)

    else:
        print("Filetype is not recognized.")

    # SAVE STATE
    data[filename] = {"chapter": cpt, "linecounter": lct,
                      "slow_print": slow_print,
                      "print_speed": print_speed}

    with open('dr-state.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

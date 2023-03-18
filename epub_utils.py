class EPUB:
    def __init__(self, chapters, linecounter, chapter):
        self.filetype = "epub"
        self.chapters = chapters
        self.linecounter = linecounter
        self.chapter = chapter
        self.textfile = self.make_textfile()

    def make_textfile(self):
        textfile = []
        counter = 0

        for i in self.chapters:
            for line in self.get_lines(counter):
                textfile.append(line)
            counter += 1

        return textfile

    def get_lines(self, chapter="current"):
        import re

        if chapter == "current":
            chapter = self.chapter

        chapter_name = list(self.chapters.keys())[chapter]
        text = self.chapters[chapter_name].replace("-\n", "")
        text = text.replace("\n", " ").replace("  ", " ")
        punctuation = re.compile(r"([^\d+])(\.|!|\?|;|\n|。|！|？|；|…|　|!|؟|؛)+")
        lines = []
        lines = punctuation.sub(r"\1\2<pad>", text)
        lines = [line.strip() for line in lines.split("<pad>") if line.strip()]

        return lines

    def get_progress(self):
        lines_read = []
        counter = 0

        for i in self.chapters:
            if counter < self.chapter:
                for line in self.get_lines(counter):
                    lines_read.append(line)
            counter += 1

        progress = (len(lines_read) + self.linecounter) / len(self.textfile)
        progress = (progress * 100).__floor__()
        progress = f"{list(self.chapters.keys())[self.chapter]} {progress}% "

        return progress

    def jump_to(self, progress):
        lines_read = int(progress * len(self.textfile) / 100)
        counter = 0
        chapter = 0

        for i in self.chapters:
            chapter_linecounter = len(self.get_lines(chapter))
            if (chapter_linecounter + counter) <= lines_read:
                counter += chapter_linecounter
                chapter += 1
            else:
                break

        linecounter = lines_read - counter

        return linecounter, chapter

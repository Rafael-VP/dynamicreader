class PDF:
    def __init__(self, chapters, linecounter, chapter):
        self.chapters = chapters
        self.linecounter = linecounter
        self.chapter = chapter

    def get_lines(self):
        import re

        text = self.chapters[self.chapter].replace("-\n", "")
        text = text.replace("\n", " ").replace("  ", " ")
        punctuation = re.compile(r"([^\d+])(\.|!|\?|;|\n|。|！|？|；|…|　|!|؟|؛)+")
        lines = []
        lines = punctuation.sub(r"\1\2<pad>", text)
        lines = [line.strip() for line in lines.split("<pad>") if line.strip()]

        return lines

    def get_progress(self):
        progress = f"{self.chapter+1}/{len(self.chapters)} "

        return progress

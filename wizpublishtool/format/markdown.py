import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension


# First create the treeprocessor
class ImgExtractor(Treeprocessor):
    def run(self, doc):
        "Find all images and append to markdown.images. "
        self.md.images = []
        for image in doc.findall('.//img'):
            self.md.images.append(image.get('src'))


# Then tell markdown about it
class ImgExtExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        img_ext = ImgExtractor(md)
        md.treeprocessors.add('imgext', img_ext, '>inline')


def find_all_images_in_md(markdown_data):
    md = markdown.Markdown(extensions=[ImgExtExtension()])
    md.convert(markdown_data)
    return md.images


def markdown_to_html(markdown_text):
    md = markdown.Markdown(extensions=[ImgExtExtension()])
    return md.convert(markdown_text)

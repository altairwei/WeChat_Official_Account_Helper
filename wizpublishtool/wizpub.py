#!/usr/bin/env python3

import os
import json
import html
import urllib
import argparse
import click
import requests
import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension

from wizpublishtool.api.wechat.material import (
    get_access_token, query_image, upload_image)


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


def get_appid_secret(appid_file):
    with open(appid_file, "r") as apf:
        AppID = apf.readline().strip()
        AppSecret = apf.readline().strip()
    return AppID, AppSecret


def markdown_to_html(markdown_text):
    md = markdown.Markdown(extensions=[ImgExtExtension()])
    return md.convert(markdown_text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Publish articles to Internet.")
    parser.add_argument("-i", "--appid-file", default="appid.txt",
                        help="Your account identity.")
    parser.add_argument("-t", "--title", help="Your account identity.")
    parser.add_argument(
        "index_file",
        help="The index file that contains the article to be published.")
    args = parser.parse_args()

    identity = get_appid_secret(args.appid_file)
    access_token = get_access_token(identity)
    # Upload markdown images
    with open(args.index_file) as inf:
        index_dirname = os.path.dirname(args.index_file)
        markdown_data = inf.read()
        images = find_all_images_in_md(markdown_data)
        # These images won't be uploaded to material, so they can not be queried
        #   through material API.
        try:
            with open(os.path.join(index_dirname, "uploaded_imgs.json"), 'r') as fh:
                uploaded_imgs = json.load(fh)
        except FileNotFoundError:
            uploaded_imgs = dict()

        for image in images:
            if image in uploaded_imgs:
                # Get img url from cache
                print("Image has been uploaded: %s" % image)
                img_url = uploaded_imgs[image]
                print(img_url)
                markdown_data = markdown_data.replace(image, img_url)
            else:
                # Upload img and cache url
                print("Uploading image: %s" % image)
                img_json = upload_image(access_token,
                                        os.path.join(index_dirname, image))
                img_url = img_json["url"]
                uploaded_imgs[image] = img_url
                print(img_url)
                markdown_data = markdown_data.replace(image, img_url)
        # Write image url cache
        with open(os.path.join(index_dirname, "uploaded_imgs.json"), 'w') as fh:
            json.dump(uploaded_imgs, fh)
        # Write processed markdown file
        with open(os.path.join(index_dirname, "processed.md"), 'w') as f:
            f.write(markdown_data)

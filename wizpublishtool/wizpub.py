#!/usr/bin/env python3

import os
import json
import html
import urllib
import argparse
import click
import requests

from wizpublishtool.api.wechat.material import (
    get_access_token, query_image, upload_image)
from wizpublishtool.api.wechat.access_token import AccessToken
from wizpublishtool.format.markdown import find_all_images_in_md


@click.group()
def wizpub():
    pass


@wizpub.group()
@click.option(
    "-i", "--appid-file", default="appid.txt", type=click.File(mode="r"))
@click.pass_context
def wechat(ctx, appid_file):
    """Publish articles to WeChat Official Account."""
    ctx.ensure_object(dict)
    # Read acount identity
    AppID = appid_file.readline().strip()
    AppSecret = appid_file.readline().strip()
    # Get acess token
    token = AccessToken(AppID, AppSecret)
    ctx.obj["token"] = token


@wechat.command()
@click.argument("index_file", type=click.Path(exists=True, readable=True))
@click.pass_context
def procmd(ctx, index_file):
    token = ctx.obj["token"]
    # Upload markdown images
    with open(index_file, "r", encoding="utf-8") as inf:
        index_dirname = os.path.dirname(index_file)
        index_basename = os.path.basename(index_file)
        index_name = os.path.splitext(index_basename)[0]
        cache_json_file = os.path.join(
            index_dirname, "%s_uploaded_imgs.json" % index_name)
        processed_md_file = os.path.join(
            index_dirname, "%s_processed.md" % index_name)
        markdown_data = inf.read()
        images = find_all_images_in_md(markdown_data)
        # These images won't be uploaded to material, so they can not be
        # queried through material API.
        try:
            with open(cache_json_file, 'r') as fh:
                uploaded_imgs = json.load(fh)
        except FileNotFoundError:
            uploaded_imgs = dict()
        # Upload and convert markdown image links
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
                img_json = upload_image(token.get_access_token(),
                                        os.path.join(index_dirname, image))
                img_url = img_json["url"]
                uploaded_imgs[image] = img_url
                print(img_url)
                markdown_data = markdown_data.replace(image, img_url)
        # Write image url cache
        with open(cache_json_file, 'w') as fh:
            json.dump(uploaded_imgs, fh)
        # Write processed markdown file
        with open(processed_md_file, 'w', encoding="utf-8") as f:
            f.write(markdown_data)

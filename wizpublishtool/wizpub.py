#!/usr/bin/env python3

import os
import shutil
import pathlib
import json
import html
import urllib
import argparse
from pathlib import Path

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
    "-i", "--appid-file", type=click.File(mode="r"))
@click.pass_context
def wechat(ctx, appid_file):
    """Publish articles to WeChat Official Account."""
    ctx.ensure_object(dict)
    # Read acount identity
    if appid_file:
        AppID = appid_file.readline().strip()
        AppSecret = appid_file.readline().strip()
    else:
        AppID = click.prompt('AppID')
        AppSecret = click.prompt('AppSecret', hide_input=True)
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


@wizpub.command()
@click.option("--res-folder", default="index_files", show_default=True,
              help="Define the name of resources folder.")
@click.argument(
    "markdown_files", type=click.File('r', encoding="utf-8"),
    nargs=-1, required=True)
@click.argument("dest_folder", nargs=1, type=click.Path())
def pack(markdown_files, dest_folder, res_folder):
    """
    Parse markdown file and package it to a directory.

    MARKDOWN_FILES accept any number of markdown files, and they will be
    processed sequentially. DEST_FOLDER is where markdown package folder will
    be placed on.

    Examples:

        wizpub pack path/to/Hello.md path/to/World.md ~/Desktop
        
        wizpub pack path/to/*.md ~/Desktop

    """
    # Create destination folder if needed
    os.makedirs(dest_folder, exist_ok=True)
    # Parse all markdown files
    for md_file in markdown_files:
        # Create markdown package folder
        md_dirname = os.path.dirname(md_file.name)
        md_basename = os.path.basename(md_file.name)
        folder_name = os.path.splitext(md_basename)[0]
        md_index_prefix = os.path.join(dest_folder, folder_name)
        os.makedirs(md_index_prefix, exist_ok=True)
        # Collect all images
        md_index_filename = os.path.join(md_index_prefix, md_basename)
        md_text = md_file.read()
        md_images = find_all_images_in_md(md_text)
        # Save images to package folder
        md_index_res_folder = os.path.join(md_index_prefix, res_folder)
        if md_images:
            os.makedirs(md_index_res_folder, exist_ok=True)
        for image in md_images:
            # Image usually is relative to markdown index file
            img_src_rel_filename = os.path.join(md_dirname, image)
            if os.path.exists(img_src_rel_filename):
                img_src_filename = img_src_rel_filename
            elif os.path.exists(image):
                # Absolute path of image
                img_src_filename = image
                pass
            else:
                click.echo("Image does not exists: %s" % image)
                # TODO: download online images
                continue
            img_dest_filename = os.path.join(
                md_index_res_folder, os.path.basename(image))
            img_src_filename = os.path.normpath(img_src_filename)
            click.echo("Copying image: %s" % img_src_filename)
            shutil.copyfile(img_src_filename, img_dest_filename)
            # Relative to markdown index file
            # TODO: Let the user decide whether to put ./ in front of it.
            img_dest_rel_filename = "./%s/%s" % (res_folder, os.path.basename(image))
            md_text = md_text.replace(image, img_dest_rel_filename)
        # Save markdown to package folder
        with open(md_index_filename, 'w', encoding="utf-8") as outf:
            outf.write(md_text)

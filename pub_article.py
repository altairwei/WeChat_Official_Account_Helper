#!/usr/bin/env python3

import os
import json
import urllib
import argparse
import requests
import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension

ACESS_TOKEN_API_URL = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
MATERIAL_COUNT_API_URL = "https://api.weixin.qq.com/cgi-bin/material/get_materialcount?access_token={ACCESS_TOKEN}"
MATERIAL_LIST_API_URL = "https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token={ACCESS_TOKEN}"
MATERIAL_ADD_API_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={ACCESS_TOKEN}&type={TYPE}"
MATERIAL_NEWS_API_URL = "https://api.weixin.qq.com/cgi-bin/material/add_news?access_token={ACCESS_TOKEN}"
IMAGE_UPLOAD_API_URL = "https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={ACCESS_TOKEN}"

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

def ensure_success(res_json):
    if "errcode" in res_json:
        raise Exception(res_json)

def get_res_body_json(response):
    res_json = response.json()
    ensure_success(res_json)
    return res_json

def get_appid_secret(appid_file):
    with open(appid_file, "r") as apf:
        AppID = apf.readline().strip()
        AppSecret = apf.readline().strip()
    return AppID, AppSecret

def get_access_token(identity):
    api_url = ACESS_TOKEN_API_URL.format(
        APPID=identity[0],
        APPSECRET=identity[1]
    )
    response = requests.get(url=api_url)
    res_json = get_res_body_json(response)

    return res_json["access_token"]

def find_image_media_id(image_name, item_json_array):
    for item in item_json_array:
        if item["name"] == image_name:
            return item
    
    return None

def query_image(image_name, access_token):
    # Get total image count
    api_url = MATERIAL_COUNT_API_URL.format(ACCESS_TOKEN=access_token)
    response = requests.get(url=api_url)
    res_json = get_res_body_json(response)
    image_count = res_json["image_count"]
    # Loop existed images
    offset = 0
    item_count = 0
    api_url = MATERIAL_LIST_API_URL.format(ACCESS_TOKEN=access_token)
    while offset < image_count:
        response = requests.post(api_url, json = {
            "type": "image",
            "offset": offset,
            "count": 20
        })
        res_json = get_res_body_json(response)
        item_count += res_json["item_count"]
        image_json = find_image_media_id(image_name, res_json["item"])
        if image_json:
            return image_json
        # Move offset to next point
        offset += 20

    return None

def upload_image_to_material(access_token, image_file):
    api_url = MATERIAL_ADD_API_URL.format(
        ACCESS_TOKEN = access_token,
        TYPE = "image"
    )
    with open(image_file, "rb") as imgf:
        media = {"media": imgf}
        response = requests.post(api_url, files=media)
        return get_res_body_json(response)

def upload_image(access_token, image_file):
    api_url = IMAGE_UPLOAD_API_URL.format(
        ACCESS_TOKEN = access_token
    )
    with open(image_file, "rb") as imgf:
        media = {"media": imgf}
        response = requests.post(api_url, files=media)
        return get_res_body_json(response)

def upload_article(access_token, markdown_text, title, thumb_media_id, ):
    api_url = MATERIAL_NEWS_API_URL.format(
        ACCESS_TOKEN = access_token
    )
    response = requests.post(api_url, data=json.dumps({
        "articles": [{
            "title": title,
            "thumb_media_id": thumb_media_id,
            "show_cover_pic": 0,
            "content": markdown_text,
            "content_source_url": "",
        }]
    }, ensure_ascii=False).encode('utf-8'))
    return get_res_body_json(response)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Publish articles to WeChat "
        "official account.")
    parser.add_argument("-i", "--appid-file", default="appid.txt",
        help="Your account identity.")
    parser.add_argument("-t", "--title", help="Your account identity.")
    parser.add_argument("index_file", help="The index file that contains the"
        " article to be published.")
    args = parser.parse_args()

    identity = get_appid_secret(args.appid_file)
    access_token = get_access_token(identity)
    query_image("Windows_Typora_Setting.png", access_token)
    # Upload markdown images
    with open(args.index_file) as inf:
        index_dirname = os.path.dirname(args.index_file)
        markdown_data = inf.read()
        images = find_all_images_in_md(markdown_data)
        # 使用这个接口“上传图文消息内的图片获取URL“而不是上传到素材库
        for image in images:
            existed_img = query_image(os.path.basename(image), access_token)
            if existed_img:
                print("Image existed in your account: %s" % image)
                img_url = existed_img["url"]
                print(img_url)
                markdown_data = markdown_data.replace(image, img_url)
            else:
                print("Uploading image: %s" % image)
                img_json = upload_image(access_token, 
                    os.path.join(index_dirname, image))
                img_url = img_json["url"]
                print(img_url)
                markdown_data = markdown_data.replace(image, img_url)

        upload_article(access_token, markdown_data, args.title, 
            query_image("paper-3033204_1280.jpg", access_token)["media_id"])

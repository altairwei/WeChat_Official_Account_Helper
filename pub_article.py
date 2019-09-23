#!/usr/bin/env python3

import argparse
import requests

ACESS_TOKEN_API_URL = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
TOTAL_MATERIAL_API_URL = "https://api.weixin.qq.com/cgi-bin/material/get_materialcount?access_token={ACCESS_TOKEN}"
MATERIAL_LIST_API_URL = "https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token={ACCESS_TOKEN}"

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
    api_url = TOTAL_MATERIAL_API_URL.format(ACCESS_TOKEN=access_token)
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Publish articles to WeChat "
        "official account.")
    parser.add_argument("-i", "--appid-file", default="appid.txt",
        help="Your account identity.")
    parser.add_argument("index_file", help="The index file that contains the"
        " article to be published.")
    args = parser.parse_args()

    identity = get_appid_secret(args.appid_file)
    access_token = get_access_token(identity)
    query_image("Windows_Typora_Setting.png", access_token)
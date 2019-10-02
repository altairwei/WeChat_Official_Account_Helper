import requests

ACESS_TOKEN_API_URL = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
MATERIAL_COUNT_API_URL = "https://api.weixin.qq.com/cgi-bin/material/get_materialcount?access_token={ACCESS_TOKEN}"
MATERIAL_LIST_API_URL = "https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token={ACCESS_TOKEN}"
MATERIAL_ADD_API_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={ACCESS_TOKEN}&type={TYPE}"
MATERIAL_DEL_API_URL = "https://api.weixin.qq.com/cgi-bin/material/del_material?access_token={ACCESS_TOKEN}"
MATERIAL_NEWS_API_URL = "https://api.weixin.qq.com/cgi-bin/material/add_news?access_token={ACCESS_TOKEN}"
IMAGE_UPLOAD_API_URL = "https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={ACCESS_TOKEN}"

def ensure_success(res_json):
    if "errcode" in res_json:
        if not res_json["errcode"] == 0:
            raise Exception(res_json)

def get_res_body_json(response):
    res_json = response.json()
    ensure_success(res_json)
    return res_json

def find_image_media_id(image_name, item_json_array):
    for item in item_json_array:
        if item["name"] == image_name:
            return item
    
    return None

def get_access_token(identity):
    api_url = ACESS_TOKEN_API_URL.format(
        APPID=identity[0],
        APPSECRET=identity[1]
    )
    response = requests.get(url=api_url)
    res_json = get_res_body_json(response)

    return res_json["access_token"]

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

def remove_image(access_token, media_id):
    api_url = MATERIAL_DEL_API_URL.format(
        ACCESS_TOKEN=access_token
    )
    response = requests.post(api_url, json = {
        "media_id":media_id
    })
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
import urllib
import time
import json
import requests

from docpub.api.wechat.wechat_resp import WechatResp

ACESS_TOKEN_API_URL = (
    "https://api.weixin.qq.com/cgi-bin/token?grant_type="
    "client_credential&appid={APPID}&secret={APPSECRET}")


class AccessToken(object):
    def __init__(self, appId, appSecret):
        self.__appId = appId
        self.__appSecret = appSecret
        self.__accessToken = ''
        self.__expiredTime = 0

    def __real_get_access_token(self):
        postUrl = ACESS_TOKEN_API_URL.format(
            APPID=self.__appId,
            APPSECRET=self.__appSecret
        )
        resp = WechatResp(requests.get(url=postUrl))
        result = resp.json()
        self.__accessToken = result['access_token']
        # Set expired time to two hours (7200 seconds) later
        self.__expiredTime = time.time() + int(result['expires_in'])

    def get_access_token(self):
        # Check if the token has expired
        if self.__expiredTime < time.time():
            self.__real_get_access_token()
        return self.__accessToken

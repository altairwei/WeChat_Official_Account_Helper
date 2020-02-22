import hmac
import base64
import time
import urllib
import webbrowser
from urllib.parse import quote, urlencode

import click
import requests

from docpub.api.yuque import LARK_HOST


def auth(clientId, clientSecret, code,
         host=LARK_HOST, scope='', log=click.echo):
    query = {
        'client_id': clientId,
        'scope': scope,
        'code': code,
        'response_type': 'code',
        'timestamp': str(int(round(time.time() * 1000))),
    }
    query['sign'] = sign(query, clientSecret)
    url = "{host}/oauth2/authorize?{querystring}".format(
        host=host, querystring=urlencode(query))
    try:
        webbrowser.open_new_tab(url)
    except webbrowser.Error:
        log("[WARING] 尝试自动打开浏览器失败: %s" % Error)
        log("[WARING] 请复制链接到浏览器中打开完成授权: %s" % url)
    # Wait and try to get token
    return getToken(clientId, host, query['code'])


def getToken(clientId, host, code):
    url = "%s/oauth2/token" % host
    interval = 3
    # 120s time out
    maxRetry = 20
    retry = 0

    for i in range(maxRetry):
        retry = retry + 1
        if retry > maxRetry:
            raise Exception("request token timeout")
        resp = requests.post(url, json={
            'code': code, 'client_id': clientId, 'grant_type': 'client_code'})
        if resp.status_code != 200 and resp.status_code != 400:
            raise Exception(
                "request yuque server with error status %i" % resp.status_code)
        elif resp.status_code == 200:
            return resp.json()
        else:
            time.sleep(interval)


def sign(query: dict, secret: str):
    signString = "&".join(
        map(lambda key: "%s=%s" % (key, quote(query.get(key, ""), safe='')),
            ['client_id', 'code', 'response_type', 'scope', 'timestamp']))
    hash_obj = hmac.new(secret.encode('utf-8'), digestmod="sha1")
    hash_obj.update(signString.encode('utf-8'))
    return base64.b64encode(hash_obj.digest()).decode("ascii")

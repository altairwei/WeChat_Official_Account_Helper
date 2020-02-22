import hmac
import base64
import time
import urllib
import webbrowser
from urllib.parse import quote, urlencode

import click
import requests
import confuse
from requests.exceptions import HTTPError

import docpub.util.settings as settings
from docpub.util.stringtool import randomString
from docpub.api.yuque import LARK_HOST


def get_token():
    # Get cached token
    try:
        return settings.config["API"]["yuque"]["token"].get()
    except confuse.NotFoundError:
        setup_auth()
        return settings.config["API"]["yuque"]["token"].get()


def setup_auth(scope):
    # Get cached client id
    try:
        client_id = settings.config["API"]["yuque"]["client_id"].get()
    except confuse.NotFoundError:
        client_id = click.prompt('Client Id')
        settings.config["API"]["yuque"]["client_id"].set(client_id)
    # Get client secret
    client_secret = click.prompt('Client Secret', hide_input=True)
    code = randomString(40)
    resp = auth(client_id, client_secret, code, scope=scope)
    # Cache token
    token = resp["access_token"]
    settings.config["API"]["yuque"]["token"].set(token)
    settings.save_config()


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
    click.echo("Waiting for authorization...")
    return waitfor_token(clientId, host, query['code'])


def request_token(clientId, host, code):
    url = "%s/oauth2/token" % host
    resp = requests.post(url, json={
        'code': code, 'client_id': clientId, 'grant_type': 'client_code'})
    resp.raise_for_status()
    return resp.json()


def waitfor_token(clientId, host, code):
    url = "%s/oauth2/token" % host
    interval = 3
    # 120s time out
    maxRetry = 20
    retry = 0

    while True:
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

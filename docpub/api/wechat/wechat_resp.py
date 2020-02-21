
class WechatError(Exception):
    pass


class WechatResp(object):
    """Wrap response and ensure success."""
    def __init__(self, response):
        res_json = response.json()
        if "errcode" in res_json:
            if not res_json["errcode"] == 0:
                raise WechatError(res_json["errmsg"])
        self.__json = res_json

    def json(self):
        return self.__json

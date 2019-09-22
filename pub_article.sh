#!/usr/bin/env bash
#
#   Dependencies: 
#       - httpie
#       - jq

# Get AppID and AppSecret
AppID=$(head -n 1 appid.txt)
AppSecret=$(tail -n 1 appid.txt)

# Get Acess Token
ACESS_TOKEN_API_URL="https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${AppID}&secret=${AppSecret}"
res_json=$(http --print b ${ACESS_TOKEN_API_URL})
access_token=$(printf ${res_json} | jq -r '.access_token')

# Get all materials
API_URL="https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token=${access_token}"
res_json=$(http -p b -j ${API_URL} type=image offset=0 count=5)
echo ${res_json} | jq .


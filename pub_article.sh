#!/usr/bin/env bash
#
#   Dependencies: 
#       - httpie
#       - jq

# Parse args
index_file=$1
index_file_basename=$(basename "${index_file}")
index_dirname=$(dirname "${index_file}")
index_temp_file="${index_dirname}/${index_file_basename}.tmp"
cat "${index_file}" > "${index_temp_file}"

# Get AppID and AppSecret
AppID=$(head -n 1 appid.txt)
AppSecret=$(tail -n 1 appid.txt)

# Get Acess Token
ACESS_TOKEN_API_URL="https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${AppID}&secret=${AppSecret}"
res_json=$(http --print b ${ACESS_TOKEN_API_URL})
access_token=$(printf ${res_json} | jq -r '.access_token')

# Get all materials
#API_URL="https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token=${access_token}"
#res_json=$(http -p b -j ${API_URL} type=image offset=0 count=5)
#echo ${res_json} | jq .

upload_image() {
    local image_file=$1
    local API_URL="https://api.weixin.qq.com/cgi-bin/material/add_news?access_token=${access_token}"

}

query_image() {
    # Get image count
    local api_url="https://api.weixin.qq.com/cgi-bin/material/get_materialcount?access_token=${access_token}"
    local res_json=$(http --print b ${api_url})
    local image_count=$(printf ${res_json} | jq -r '.image_count')
    # Get image list
    local api_url="https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token=${access_token}"
    while (( image_count > 0 )); do
        local res_json=$(http -p b -j ${api_url} type=image offset=0 count=20)
        image_count=$((image_count - 20))
    done
    }

# Parse image urls from markdwn file

while read url; do
    printf 'Uploading image: %s\n' "${url}"
    #TODO: upload images
    
    sed -E -e "s/${url}//"
done < <(cat "${index_file}" | sed -nE -e 's/.*!\[.*\]\((.*)\).*/\1/p')


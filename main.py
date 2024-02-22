import json
from typing import Optional
import requests
from fastapi import FastAPI, Request
from pydantic import BaseModel
from linebot import WebhookHandler

import config
from calculator import calculate

app = FastAPI()


class UserInput(BaseModel):
    operation: str
    x: float
    y: float


@app.get("/")
async def root():
    print('Hello World')
    return {"message": "Hello World"}


@app.get('/version')
def version():
    return {"version": "0.0.1.240222.1"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}


@app.post('/calculate')
def operate(input: UserInput):
    print(input)
    result = calculate(input.operation, input.x, input.y)
    return result


@app.post('/linebot')
async def linebot(input: Request) -> str:
    # line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(config.LINE_CHANNEL_SECRET)
    # 處理 LINE BOT 事件
    signature = input.headers['X-Line-Signature']
    json_data = await input.json()
    body = await input.body()
    handler.handle(body.decode(), signature)
    print(json_data)

    if events := json_data['events']:
        reply_token = events[0]['replyToken']
        message_type = events[0]['message']['type']
        if message_type == 'text':
            msg = events[0]['message']['text']
            # line_bot_api.reply_message(reply_token, TextSendMessage(text=msg))
            if msg in ['雷達回波', '雷達回波圖']:
                # # 臺灣(鄰近區域)_無地形
                # radar_url = 'https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/O-A0058-003?Authorization=rdec-key-123-45678-011121314&format=JSON'
                # radar = requests.get(radar_url)
                # radar_json = radar.json()
                # im_url = radar_json['cwaopendata']['dataset']['resource']['ProductURL']
                im_url = 'https://cwaopendata.s3.ap-northeast-1.amazonaws.com/Observation/O-A0058-003.png'
                reply_image(im_url, reply_token)
    return 'OK'


# LINE 回傳圖片函式
def reply_image(im_url, reply_token):
    headers = {'Authorization': f'Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}', 'Content-Type': 'application/json'}
    body = {
        'replyToken': reply_token,
        'messages': [{
            'type': 'image',
            'originalContentUrl': im_url,
            'previewImageUrl': im_url
            }]
    }
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/reply',
                           headers=headers,
                           data=json.dumps(body).encode('utf-8'))
    print(req.text)

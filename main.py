import json
import time
from typing import Optional
import requests
import pandas as pd
from fastapi import FastAPI, Request
from pydantic import BaseModel
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageAction, URIAction, TemplateSendMessage, CarouselTemplate, CarouselColumn

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
    return {"version": "0.0.1.240222.9"}


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
    line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
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
                im_url = f'https://cwaopendata.s3.ap-northeast-1.amazonaws.com/Observation/O-A0058-003.png?{time.time_ns()}'
                reply_image(im_url, reply_token)
            elif msg in ['地震']:
                df = earth_quake()
                columns = []
                for idx, row in df.iterrows():
                    # df['description'] = df['EarthquakeInfo.OriginTime'] + \
                    #     df['EarthquakeInfo.Epicenter.Location'] + \
                    #     '深度:'+df['EarthquakeInfo.FocalDepth'].astype(str) + \
                    #     df['EarthquakeInfo.EarthquakeMagnitude.MagnitudeType'] + \
                    #     df['EarthquakeInfo.EarthquakeMagnitude.MagnitudeValue'].astype(str)
                    magnitude = f"{row['EarthquakeInfo.EarthquakeMagnitude.MagnitudeType']}: {row['EarthquakeInfo.EarthquakeMagnitude.MagnitudeValue']}"
                    depth = f"深度:{row['EarthquakeInfo.FocalDepth']} 公里"
                    carousel_column = CarouselColumn(
                        thumbnail_image_url=row.ReportImageURI,
                        title=row['EarthquakeInfo.Epicenter.Location'],
                        text=magnitude,
                        actions=[
                            MessageAction(label=depth, text=depth),
                            URIAction(label='前往查看', uri=row['Web'])
                        ]
                    )
                    columns.append(carousel_column)
                # prepare to send reply message
                template_send_message = TemplateSendMessage(
                    alt_text='CarouselTemplate',
                    template=CarouselTemplate(
                        columns=columns
                    )
                )
                line_bot_api.reply_message(reply_token, template_send_message)
        elif message_type == 'location':
            address = events[0]['message']['address'].replace('台', '臺')  # 氣象局都用 "臺"
            print(address)
            df = taiwan_weather(address)
            columns = []
            for idx, row in df.iterrows():
                img_url = 'https://upload.wikimedia.org/wikipedia/commons/7/72/Wikinews_weather.png'
                weather = f"{row['WeatherElement.Weather']}: {row['WeatherElement.AirTemperature']}度 \
                    最高: {row['WeatherElement.DailyExtreme.DailyHigh.TemperatureInfo.AirTemperature']}\
                    最低: {row['WeatherElement.DailyExtreme.DailyLow.TemperatureInfo.AirTemperature']}"
                humidity = f"相對溼度: {row['WeatherElement.RelativeHumidity']}"
                carousel_column = CarouselColumn(
                    thumbnail_image_url=img_url,
                    title=row['address'],
                    text=weather,
                    actions=[
                        MessageAction(label=row['StationName'], text=row['StationName']),
                        MessageAction(label=humidity, text=humidity)
                    ]
                )
                columns.append(carousel_column)
            # prepare to send reply message
            template_send_message = TemplateSendMessage(
                alt_text='CarouselTemplate',
                template=CarouselTemplate(
                    columns=columns
                )
            )
            line_bot_api.reply_message(reply_token, template_send_message)
    return 'OK'


# 地震資訊函式
def taiwan_weather(address):
    """取得地震資料
    https://opendata.cwa.gov.tw/index
    /v1/rest/datastore/O-A0001-001 自動氣象站
    /v1/rest/datastore/O-A0003-001 現在天氣觀測報告-有人氣象站資料

    Returns:
        _type_: _description_

    StationName: 鼻頭, 興海
    GeoInfo.CountyName: 屏東縣
    GeoInfo.TownName: 滿州鄉
    WeatherElement.Weather: 晴

    df['StationName']        # 觀測站
    df['GeoInfo.CountyName'] # 縣市
    df['GeoInfo.TownName']   # 城鎮
    df['WeatherElement.Weather']        # 天氣
    df['WeatherElement.WindDirection']  # 風向
    df['WeatherElement.WindSpeed']      # 風速
    df['WeatherElement.DailyExtreme.DailyHigh.TemperatureInfo.AirTemperature'] # 最高
    df['WeatherElement.DailyExtreme.DailyLow.TemperatureInfo.AirTemperature']  # 最低
    df['WeatherElement.AirTemperature'] # 氣溫
    df['WeatherElement.RelativeHumidity'] # 相對濕度
    """
    code = config.OPENDATA_CWA_GOV
    url1 = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization={code}'  # 自動氣象站
    url2 = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={code}'  # 有人氣象站
    e_data = requests.get(url1)
    e_data_json = e_data.json()
    df1 = pd.json_normalize(data=e_data_json['records'], record_path='Station')

    e_data = requests.get(url2)
    e_data_json = e_data.json()
    df2 = pd.json_normalize(data=e_data_json['records'], record_path='Station')
    df2.drop(set(df2.columns) - set(df1.columns), axis=1, inplace=True)  # 確保欄位相同

    df3 = pd.concat([df1, df2], axis=0)
    df3['address'] = df3['GeoInfo.CountyName'] + df3['GeoInfo.TownName']

    return df3.query('address in @address')


# 地震資訊函式
def earth_quake():
    """取得地震資料
    https://opendata.cwa.gov.tw/index
    /v1/rest/datastore/E-A0015-001 顯著有感地震報告資料
    /v1/rest/datastore/E-A0016-001 小區域有感地震報告資料

    Returns:
        _type_: _description_
    """
    code = config.OPENDATA_CWA_GOV
    url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0016-001?Authorization={code}'
    e_data = requests.get(url)
    e_data_json = e_data.json()

    df = pd.json_normalize(data=e_data_json['records'], record_path='Earthquake')
    # 地震深度超過 30 公里
    df = df[df['EarthquakeInfo.FocalDepth'] > 30]
    # if not df.empty:
    #     df['description'] = df['EarthquakeInfo.OriginTime'] + \
    #         df['EarthquakeInfo.Epicenter.Location'] + \
    #         '深度:'+df['EarthquakeInfo.FocalDepth'].astype(str) + \
    #         df['EarthquakeInfo.EarthquakeMagnitude.MagnitudeType'] + \
    #         df['EarthquakeInfo.EarthquakeMagnitude.MagnitudeValue'].astype(str)
    #     df = df[['ReportImageURI', 'description']]
    return df


# LINE 回傳圖片函式
def reply_image(im_url, reply_token):
    print(f'DEBUG {config.LINE_CHANNEL_ACCESS_TOKEN=}')
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


# LINE 回傳訊息函式
def reply_message(msg, reply_token):
    headers = {'Authorization': f'Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}', 'Content-Type': 'application/json'}
    body = {
        'replyToken': reply_token,
        'messages': [{
            "type": "text",
            "text": msg
            }]
    }
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/reply',
                           headers=headers,
                           data=json.dumps(body).encode('utf-8'))
    print(req.text)

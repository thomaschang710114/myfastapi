from typing import Optional

from fastapi import FastAPI, Request
from pydantic import BaseModel
from linebot import LineBotApi, WebhookHandler

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
    line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(config.LINE_CHANNEL_SECRET)
    json_data = await input.json()
    print(json_data)
    return 'OK'

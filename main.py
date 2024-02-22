from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

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

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.post('/calculate')
def operate(input: UserInput):
    print(input)
    result = calculate(input.operation, input.x, input.y)
    return result

from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel
from controllers import livestock_tracker

app = FastAPI()

class Livestock(BaseModel):
    livestock_type: str
    health_status: str
    group_name: str
    age: int
    expected_growth: int

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/api/livestock/add")
def add_livestock(livestock: Livestock):
    return livestock_tracker.add_livestock(livestock.livestock_type, livestock.health_status, livestock.group_name, livestock.age, livestock.expected_growth)

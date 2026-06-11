import random

from fastapi import FastAPI

app = FastAPI()

HOME_MESSAGES = [
    "Welcome to the silly site!",
    "Hello, world!",
    "You found the home page.",
    "Glad you're here.",
]

ABOUT_MESSAGES = [
    "This site is powered by FastAPI.",
    "We're a small but mighty test project.",
    "About page, at your service.",
    "Built for fun, deployed for science.",
]


@app.get("/")
def read_root():
    return {"msg": random.choice(HOME_MESSAGES)}


@app.get("/about")
def read_about():
    return {"msg": random.choice(ABOUT_MESSAGES)}

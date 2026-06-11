# Silly Site
Test for website deployment

A basic FastAPI app with two endpoints:
- `/` returns `{"msg": "<random message>"}`
- `/about` returns `{"msg": "<random message>"}`

## Running

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

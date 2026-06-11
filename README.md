# Silly Site
Test for website deployment

A basic FastAPI app with two endpoints:
- `/` returns `{"msg": "<random message>"}`
- `/about` returns `{"msg": "<random message>"}`

## Running

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn main:app --reload
```

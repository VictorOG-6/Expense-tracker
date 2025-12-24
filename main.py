from fastapi import FastAPI
from database import create_db_and_tables
from routers import auth, user, transactions

app = FastAPI()

@app.get('/health')
def health():
    return {"status": "ok"}

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(transactions.router)
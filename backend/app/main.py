from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.bots import seed_bot_teams
from app.core.database import SessionLocal
from app.core.market import refill_market
from app.core.scheduler import start_scheduler
from app.routers import admin, auth, league, market, matches, roster, sponsors, stadium, teams, trades, training, transfers

app = FastAPI(title="Gridiron Manager API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

app.include_router(auth.router)
app.include_router(teams.router)
app.include_router(training.router)
app.include_router(matches.router)
app.include_router(sponsors.router)
app.include_router(stadium.router)
app.include_router(market.router)
app.include_router(roster.router)
app.include_router(transfers.router)
app.include_router(trades.router)
app.include_router(league.router)
app.include_router(admin.router)


@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        refill_market(db)
        seed_bot_teams(db)
    finally:
        db.close()
    start_scheduler()


@app.get("/health")
def health():
    return {"status": "ok"}

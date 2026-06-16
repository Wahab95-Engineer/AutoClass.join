import os, threading
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from database import *
from scheduler import start, sync_emails
from joiner import join_meeting
from link_extractor import detect_platform

app = FastAPI()
init_db()

@app.on_event("startup")
def startup(): start()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def root():
    return open("static/index.html").read()

# ─── Schemas ─────────────────────────────────
class AccountIn(BaseModel):
    email: str; password: str; provider: str

class MeetingIn(BaseModel):
    title: Optional[str] = "Class"
    link: str; scheduled_time: str
    duration_minutes: Optional[int] = 60

class JoinIn(BaseModel):
    meeting_id: int

# ─── Routes ──────────────────────────────────
@app.get("/api/accounts")
def r_accounts():
    a = get_accounts()
    for x in a: x["password"] = "••••••"
    return a

@app.post("/api/accounts")
def r_add_account(b: AccountIn):
    host = {"gmail":"imap.gmail.com","outlook":"imap-mail.outlook.com"}.get(b.provider,"imap.gmail.com")
    add_account(b.email, b.password, b.provider, host)
    return {"ok": True}

@app.delete("/api/accounts/{aid}")
def r_del_account(aid: int):
    delete_account(aid); return {"ok": True}

@app.post("/api/accounts/sync")
def r_sync():
    threading.Thread(target=sync_emails, daemon=True).start()
    return {"ok": True}

@app.get("/api/meetings")
def r_meetings(status: Optional[str] = None):
    return get_meetings(status)

@app.post("/api/meetings")
def r_add_meeting(b: MeetingIn):
    p = detect_platform(b.link)
    if p == "Unknown": raise HTTPException(400, "Invalid meeting link")
    mid = add_meeting(b.title, b.link, p, b.scheduled_time)
    return {"ok": True, "id": mid}

@app.delete("/api/meetings/{mid}")
def r_del_meeting(mid: int):
    delete_meeting(mid); return {"ok": True}

@app.post("/api/meetings/join-now")
def r_join(b: JoinIn):
    meetings = get_meetings()
    m = next((x for x in meetings if x["id"] == b.meeting_id), None)
    if not m: raise HTTPException(404, "Not found")
    threading.Thread(target=join_meeting, args=(m, os.getenv("DISPLAY_NAME","Student")), daemon=True).start()
    return {"ok": True}

@app.get("/api/logs")
def r_logs(): return get_logs()

@app.get("/api/status")
def r_status():
    m = get_meetings()
    return {
        "total_meetings": len(m),
        "pending": sum(1 for x in m if x["status"]=="pending"),
        "joined":  sum(1 for x in m if x["status"]=="joined"),
        "failed":  sum(1 for x in m if x["status"]=="failed"),
        "accounts": len(get_accounts()),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
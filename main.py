from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase_client import supabase

app = FastAPI()

# --- MODELS ---
class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    username: str
    password: str
    role: str = "student"

class ProgressCreate(BaseModel):
    user_id: str
    letter: str
    completed: bool = True

# --- ROUTES ---
@app.get("/")
def root():
    return {"message": "Star Rise ABCs API is running"}

@app.post("/users")
def create_user(user: UserCreate):
    try:
        res = supabase.table("users").insert({
            "username": user.username,
            "password": user.password,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role
        }).execute()
        return res.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
def login_user(login: LoginRequest):
    try:
        res = supabase.table("users").select("*").eq("username", login.username).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = res.data[0]
        if user.get("password") == login.password:
            return user
        else:
            raise HTTPException(status_code=401, detail="Invalid password")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

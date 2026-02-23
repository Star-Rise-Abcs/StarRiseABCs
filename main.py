from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase_client import supabase

app = FastAPI()

# --- MODELS ---

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    firstName: str
    lastName: str
    username: str
    password: str
    role: str = "student"

class ProgressCreate(BaseModel):
    user_id: str
    letter: str
    completed: bool = True

class RewardCreate(BaseModel):
    user_id: str
    reward_name: str

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
            "first_name": user.firstName,
            "last_name": user.lastName,
            "role": user.role
        }).execute()

        if not res.data:
            raise HTTPException(status_code=400, detail="Failed to create user")
            
        return res.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
def login_user(login: LoginRequest):
    try:
        # We now query by the 'username' column
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

@app.post("/progress")
def add_progress(progress: ProgressCreate):
    try:
        res = supabase.table("progress").insert({
            "user_id": progress.user_id,
            "letter": progress.letter,
            "completed": progress.completed
        }).execute()
        return res.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rewards")
def give_reward(reward: RewardCreate):
    try:
        res = supabase.table("rewards").insert({
            "user_id": reward.user_id,
            "reward_name": reward.reward_name
        }).execute()
        return res.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

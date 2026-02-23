from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase_client import supabase  # your initialized Supabase client

app = FastAPI()

class LoginRequest(BaseModel):
    email: str
    password: str

# --- MODELS ---
class UserCreate(BaseModel):
    name: str
    role: str  # "student" or "teacher"


class ProgressCreate(BaseModel):
    user_id: str
    letter: str
    completed: bool = True


class RewardCreate(BaseModel):
    user_id: str
    reward_name: str


# --- ROOT ---
@app.get("/")
def root():
    return {"message": "Star Rise ABCs API is running"}


@app.post("/users")
def create_user(user: UserCreate):
    try:
        res = supabase.table("users").insert({
            "name": user.name,
            "role": user.role
        }).execute()

        # just return inserted user
        return res.data[0]

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

# Add this route at the bottom
@app.post("/login")
def login_user(login: LoginRequest):
    try:
        # This asks Supabase: "Find the user where the name matches the email"
        res = supabase.table("users").select("*").eq("name", login.email).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = res.data[0]
        
        # Simple text check (since we aren't hashing yet)
        if user.get("password") == login.password:
            return user
        else:
            raise HTTPException(status_code=401, detail="Invalid password")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase_client import supabase  # your initialized Supabase client

app = FastAPI()


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

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

# UPGRADED: To match your Android ProgressManager
class ProgressUpdate(BaseModel):
    user_id: str
    category: str      # 'letter', 'quiz1', 'quiz2', 'quiz3'
    item_index: int    # The letter index or question index
    stars_earned: int

class ClassUpdate(BaseModel):
    user_id: str
    class_code: str

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

# NEW: The door for your Android app to sync progress
@app.post("/update_progress")
def update_progress(data: ProgressUpdate):
    try:
        # Upsert ensures we don't get duplicates for the same letter/quiz
        res = supabase.table("progress").upsert({
            "user_id": data.user_id,
            "category": data.category,
            "item_index": data.item_index,
            "stars_earned": data.stars_earned,
            "updated_at": "now()"
        }).execute()
        return {"status": "success", "data": res.data}
    except Exception as e:
        print(f"Sync Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_class")
async def update_class(data: ClassUpdate):  # Changed 'fun' to 'def'
    try:
        res = supabase.table("users").update({
            "class_code": data.class_code
        }).eq("id", data.user_id).execute()
        
        return {"status": "success", "data": res.data}
    except Exception as e:
        print(f"Class Update Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

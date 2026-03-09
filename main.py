from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase_client import supabase
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

app = FastAPI()

# --- MIDDLEWARE ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- UNIFIED MODELS ---


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    username: str
    password: str
    role: str = "student"


class ProgressUpdate(BaseModel):
    user_id: str
    category: str
    item_index: int
    stars_earned: int


class ClassUpdate(BaseModel):
    user_id: str
    class_code: str


class RewardOption(BaseModel):
    class_code: str
    reward_name: str
    stars_required: int
    icon_type: str

# --- SHARED ROUTES  ---


@app.get("/")
def root():
    return {"message": "Star Rise ABCs Unified API is running"}


@app.post("/login")
def login_user(login: LoginRequest):
    try:
        res = supabase.table("users").select(
            "*").eq("username", login.username).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="User not found")

        user = res.data[0]
        if user.get("password") == login.password:
            return user
        else:
            raise HTTPException(status_code=401, detail="Invalid password")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ANDROID APP SPECIFIC ROUTES ---


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


@app.post("/update_progress")
def update_progress(data: ProgressUpdate):
    try:
        res = supabase.table("progress").upsert({
            "user_id": data.user_id,
            "category": data.category,
            "item_index": data.item_index,
            "stars_earned": data.stars_earned,
            "updated_at": "now()"
        }).execute()
        return {"status": "success", "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_user_progress/{user_id}")
def get_user_progress(user_id: str):
    response = supabase.table("progress").select(
        "*").eq("user_id", user_id).execute()
    return response.data


@app.post("/update_class")
async def update_class_from_app(data: ClassUpdate):
    try:
        res = supabase.table("users").update({
            "class_code": data.class_code
        }).eq("id", data.user_id).execute()
        return {"status": "success", "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- TEACHER DASHBOARD
TEACHER_ACCESS_CODE = "OLFU_STAR_RISE"


@app.post("/register_teacher")
async def register_teacher(data: dict):
    if data.get("access_code") != TEACHER_ACCESS_CODE:
        raise HTTPException(
            status_code=403, detail="Invalid Teacher Access Code")

    existing = supabase.table("users").select(
        "*").eq("username", data['username']).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = {
        "first_name": data['first_name'],
        "last_name": data['last_name'],
        "username": data['username'],
        "password": data['password'],
        "role": "teacher"
    }
    try:
        supabase.table("users").insert(new_user).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_all_classes")
def get_all_classes():
    class_res = supabase.table("classes").select(
        "class_code, creator_name").execute()
    user_res = supabase.table("users").select(
        "class_code").eq("role", "student").execute()
    student_codes = [r['class_code'] for r in user_res.data if r['class_code']]

    report = []
    for cls in class_res.data:
        code = cls['class_code']
        report.append({
            "class_code": code,
            "creator_name": cls.get('creator_name', 'System'),
            "student_count": student_codes.count(code)
        })
    return sorted(report, key=lambda x: x['class_code'])


@app.post("/create_class")
async def create_class(payload: dict):
    class_code = payload.get("class_code", "").strip().upper()
    user_id = payload.get("user_id")
    creator_name = payload.get("creator_name", "System")

    if not class_code:
        raise HTTPException(
            status_code=400, detail="Class code cannot be empty.")

    try:
        supabase.table("classes").insert({
            "class_code": class_code,
            "teacher_id": user_id,
            "creator_name": creator_name
        }).execute()

        supabase.table("reward_options").upsert({
            "class_code": class_code,
            "reward_name": "ABC Reward",
            "stars_required": 26,
            "icon_type": "abc"
        }, on_conflict="class_code,icon_type").execute()
        return {"status": "success"}
    except Exception as e:
        if "23505" in str(e):
            raise HTTPException(
                status_code=400, detail=f"The class code '{class_code}' is already taken.")
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred.")


@app.get("/get_class_report/{class_code}")
def get_class_report(class_code: str):
    # 1. Normalize the input to Uppercase so '3y2-4' and '3Y2-4' both work
    normalized_code = class_code.strip().upper()

    # 2. Query using the normalized code
    users = supabase.table("users").select("*") \
        .eq("class_code", normalized_code) \
        .eq("role", "student").execute()
    if not users.data:
        return []

    user_ids = [u['id'] for u in users.data]
    progress = supabase.table("progress").select(
        "*").in_("user_id", user_ids).execute()

    report = []
    for u in users.data:
        u_p = [p for p in progress.data if p['user_id'] == u['id']]

        report.append({
            "name": f"{u['first_name']} {u['last_name']}",
            "abc": len([p for p in u_p if p['category'] == 'letter' and p.get('stars_earned', 0) > 0]),

            "sing_along": len([p for p in u_p if p['category'] == 'sing_along' and p.get('stars_earned', 0) > 0]),

            "quiz1": len([p for p in u_p if p['category'] == 'quiz1' and p.get('stars_earned', 0) > 0]),
            "quiz2": len([p for p in u_p if p.get('category') == 'quiz2' and p.get('stars_earned', 0) > 0]),
            "quiz3": len([p for p in u_p if p['category'] == 'quiz3' and p.get('stars_earned', 0) > 0])
        })
    return report


@app.get("/search_all_students")
async def search_all_students(query: str):
    q_raw = query.strip()
    q_like = f"%{q_raw}%"
    parts = q_raw.split()

    student_query = supabase.table("users").select("*").eq("role", "student")
    if len(parts) > 1:
        student_res = student_query.ilike("first_name", f"%{parts[0]}%").ilike(
            "last_name", f"%{parts[1]}%").execute()
    else:
        student_res = student_query.or_(
            f"first_name.ilike.{q_like},last_name.ilike.{q_like},username.ilike.{q_like}").execute()

    class_res = supabase.table("classes").select(
        "*").ilike("class_code", q_like).execute()
    matched_classes_raw = class_res.data

    student_class_codes = list(
        set([u['class_code'] for u in student_res.data if u.get('class_code')]))
    if student_class_codes:
        existing_codes = [c['class_code'] for c in matched_classes_raw]
        missing_codes = [
            code for code in student_class_codes if code not in existing_codes]
        if missing_codes:
            extra = supabase.table("classes").select(
                "*").in_("class_code", missing_codes).execute()
            matched_classes_raw.extend(extra.data)

    all_students_res = supabase.table("users").select(
        "class_code").eq("role", "student").execute()
    all_student_codes = [r['class_code']
                         for r in all_students_res.data if r['class_code']]

    final_classes = []
    for cls in matched_classes_raw:
        code = cls['class_code']
        final_classes.append({
            "class_code": code,
            "creator_name": cls.get('creator_name', 'System'),
            "student_count": all_student_codes.count(code)
        })

    matched_students = []
    for u in student_res.data:
        u_p_res = supabase.table("progress").select(
            "*").eq("user_id", u['id']).execute()
        u_p = u_p_res.data if u_p_res.data else []

        matched_students.append({
            "name": f"{u['first_name']} {u['last_name']}",
            "class_code": u.get("class_code", "NONE"),
            "abc": len([p for p in u_p if p.get('category') == 'letter' and p.get('stars_earned', 0) > 0]),
            "sing_along": len([p for p in u_p if p.get('category') == 'sing_along' and p.get('stars_earned', 0) > 0]),
            "quiz1": len([p for p in u_p if p.get('category') == 'quiz1' and p.get('stars_earned', 0) > 0]),
            "quiz2": len([p for p in u_p if p.get('category') == 'quiz2' and p.get('stars_earned', 0) > 0]),
            "quiz3": len([p for p in u_p if p.get('category') == 'quiz3' and p.get('stars_earned', 0) > 0])
        })

    return {"matched_students": matched_students, "matched_classes": final_classes}


@app.post("/update_specific_reward")
async def update_specific_reward(data: RewardOption):
    try:
        payload = data.dict()
        supabase.table("reward_options").upsert(
            payload, on_conflict="class_code,icon_type").execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_class_rewards/{class_code}")
async def get_class_rewards(class_code: str):
    res = supabase.table("reward_options").select(
        "*").eq("class_code", class_code).execute()
    return res.data


@app.delete("/delete_class/{class_code}")
async def delete_class(class_code: str):
    try:
        supabase.table("reward_options").delete().eq(
            "class_code", class_code).execute()
        supabase.table("classes").delete().eq(
            "class_code", class_code).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_unassigned_students")
def get_unassigned_students():
    res = supabase.table("users").select(
        "id, first_name, last_name, username, class_code").eq("role", "student").execute()
    return res.data


@app.post("/assign_student_to_class")
async def assign_student_to_class(data: dict):
    try:
        supabase.table("users").update({"class_code": data.get("class_code")}).eq(
            "id", data.get("student_id")).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

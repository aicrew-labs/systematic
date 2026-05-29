import re

file_path = "backend/app/main.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Update FeedbackRequest
old_class = r"""class FeedbackRequest\(BaseModel\):
    feedback: str"""

new_class = """from typing import Optional

class FeedbackRequest(BaseModel):
    feedback: str
    status: Optional[str] = None"""

content = re.sub(old_class, new_class, content, flags=re.DOTALL)

# Update submit_feedback
old_func = r"""@app\.post\("/api/v1/auth/feedback"\)
def submit_feedback\(req: FeedbackRequest, current_user: UserInfo = Depends\(get_current_user\)\):
    from app\.database import update_user_feedback
    success = update_user_feedback\(current_user\.user_id, req\.feedback\)
    if not success:
        raise HTTPException\(status_code=500, detail="Failed to save feedback"\)
    return \{"status": "ok", "message": "Feedback saved"\}"""

new_func = """@app.post("/api/v1/auth/feedback")
def submit_feedback(req: FeedbackRequest, current_user: UserInfo = Depends(get_current_user)):
    from app.database import update_user_feedback
    success = update_user_feedback(current_user.user_id, req.feedback, req.status)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save feedback")
    return {"status": "ok", "message": "Feedback saved"}"""

content = re.sub(old_func, new_func, content, flags=re.DOTALL)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated main.py")

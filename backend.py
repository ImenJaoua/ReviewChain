# backend.py
from fastapi import FastAPI
from pydantic import BaseModel

# Import your agents — this will load ALL models ONCE and keep them in RAM
from agents_local import (
    comment_generator,
    code_refiner,
    quality_estimator,
    format_judge
)

print("\n🔥 All models loaded in backend and ready for inference.\n")

# FastAPI app
app = FastAPI()

# ================================================
# Pydantic schemas
# ================================================

class CommentRequest(BaseModel):
    code: str

class RefinementRequest(BaseModel):
    code: str
    comment: str

class QualityRequest(BaseModel):
    code: str

class FormatRequest(BaseModel):
    comment: str


# ================================================
# API ROUTES
# ================================================

@app.post("/generate_comment")
def generate_comment(req: CommentRequest):
    result = comment_generator(req.code)
    return {"response": result}

@app.post("/refine")
def refine(req: RefinementRequest):
    result = code_refiner(req.code, req.comment)
    return {"response": result}

@app.post("/quality")
def quality(req: QualityRequest):
    result = quality_estimator(req.code)
    return {"response": result}

@app.post("/format")
def format_check(req: FormatRequest):
    result = format_judge(req.comment)
    return {"response": result}


from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from supabase import create_client, Client
from fpdf import FPDF
import uuid

app = FastAPI()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = "shayajean-docs"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class PDFRequest(BaseModel):
    title: str
    content: str

@app.post("/generate-pdf")
async def generate_pdf(data: PDFRequest):
    try:
        filename = f"{uuid.uuid4()}.pdf"
        filepath = f"/tmp/{filename}"

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(190, 10, f"{data.title}

{data.content}")
        pdf.output(filepath)

        with open(filepath, "rb") as f:
            res = supabase.storage.from_(SUPABASE_BUCKET).upload(filename, f, {"content-type": "application/pdf", "cacheControl": "3600", "upsert": True})
        
        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename)

        return {"success": True, "url": public_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

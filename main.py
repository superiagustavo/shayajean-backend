from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fpdf import FPDF
import os
from supabase import create_client, Client

app = FastAPI()

# Supabase config
SUPABASE_URL = "https://eaubrpnwyzmsxxawdlqa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVhdWJycG53eXptc3h4YXdkbHFhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5MjIzMTIsImV4cCI6MjA2MDQ5ODMxMn0.zz5kWKbTpzFfjq-iw_awaLdlVjG_NuiZWh_fvaprC2A"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class PDFData(BaseModel):
    title: str
    content: str

@app.post("/generate-pdf")
def generate_pdf(data: PDFData):
    filepath = "output.pdf"
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(190, 10, f"{data.title}")
        pdf.multi_cell(190, 10, f"{data.content}")
        pdf.output(filepath)

        with open(filepath, "rb") as f:
            file_content = f.read()
            supabase.storage.from_("shayajean-docs").upload(
                path="output.pdf",
                file=file_content,
                file_options={
                    "content-type": "application/pdf",
                    "upsert": True
                }
            )

        public_url = f"{SUPABASE_URL}/storage/v1/object/public/shayajean-docs/output.pdf"
        return {"url": public_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar ou enviar PDF: {str(e)}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

@app.get("/")
def root():
    return {"message": "API rodando com sucesso!"}


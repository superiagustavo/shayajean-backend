from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fpdf import FPDF
from fastapi.responses import FileResponse
import os
from supabase import create_client, Client

app = FastAPI()

# Supabase configs
SUPABASE_URL = "https://qqfsdibkhzonymwcttjj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFxZnNkaWJraHpvbnltd2N0dGpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5Mjc5MTksImV4cCI6MjA2MDUwMzkxOX0.rRwwa8w_MLD_eVHkqsMw2hpIPj_uqxSln1EACuMf4vo"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Modelo de dados esperado
class PDFData(BaseModel):
    title: str
    content: str

@app.post("/generate-pdf")
def generate_pdf(data: PDFData):
    # Define o nome do arquivo com base no título (removendo espaços)
    nome_arquivo = f"{data.title.replace(' ', '_')}.pdf"
    filepath = f"/tmp/{nome_arquivo}"

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.multi_cell(190, 10, f"{data.title}")
        pdf.multi_cell(190, 10, f"{data.content}")

        pdf.output(filepath)

        with open(filepath, "rb") as f:
            file_content = f.read()

        # Upload no Supabase com headers corretos
        supabase.storage.from_("shayajean-docs").upload(
            nome_arquivo,
            file_content,
            {"content-type": "application/pdf"}
        )

        public_url = f"{SUPABASE_URL}/storage/v1/object/public/shayajean-docs/{nome_arquivo}"
        print(f"LOG UPLOAD: {public_url}")
        return {"url": public_url}

    except Exception as e:
        print(f"ERRO: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

@app.get("/")
def root():
    return {"message": "API operacional"}

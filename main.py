from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fpdf import FPDF
from fastapi.responses import FileResponse
import os
from supabase import create_client, Client

app = FastAPI()

# SUPABASE CONFIGS
SUPABASE_URL = "https://qqfsdibkhzonymwcttjj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFxZnNkaWJraHpvbnltd2N0dGpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5Mjc5MTksImV4cCI6MjA2MDUwMzkxOX0.rRwwa8w_MLD_eVHkqsMw2hpIPj_uqxSln1EACuMf4vo"  # <-- substitua pelo valor COMPLETO
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class PDFData(BaseModel):
    title: str
    content: str

@app.post("/generate-pdf")
def generate_pdf(data: PDFData):
    try:
        safe_title = data.title.strip().replace(" ", "_")
        filename = f"{safe_title}.pdf"
        filepath = f"/tmp/{filename}"

        # Gera o PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(190, 10, f"{data.title}")
        pdf.multi_cell(190, 10, f"{data.content}")
        pdf.output(filepath)

        # Upload para Supabase
        with open(filepath, "rb") as f:
            file_content = f.read()
            result = supabase.storage.from_("shayajean-docs").upload(
                path=filename,
                file=file_content,
                file_options={
                    "content-type": "application/pdf",
                    "upsert": True  # força sobrescrita
                }
            )

        # Gera URL pública
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/shayajean-docs/{filename}"
        return {"url": public_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar/enviar PDF: {str(e)}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@app.get("/")
def root():
    return {"message": "API ativa para geração e upload de PDFs"}

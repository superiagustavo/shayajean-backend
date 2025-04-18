from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fpdf import FPDF
import os
from fastapi.responses import JSONResponse
from supabase import create_client, Client

app = FastAPI()

# Supabase configs
SUPABASE_URL = "https://qqfsdibkhzonymwcttjj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFxZnNkaWJraHpvbnltd2N0dGpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5Mjc5MTksImV4cCI6MjA2MDUwMzkxOX0.rRwwa8w_MLD_eVHkqsMw2hpIPj_uqxSln1EACuMf4vo"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class PDFData(BaseModel):
    title: str
    content: str

@app.post("/generate-pdf")
def generate_pdf(data: PDFData):
    filename = f"{data.title.replace(' ', '_')}.pdf"
    filepath = f"/tmp/{filename}"

    try:
        # Geração do PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(190, 10, data.title)
        pdf.multi_cell(190, 10, data.content)
        pdf.output(filepath)

        # Leitura do arquivo
        with open(filepath, "rb") as f:
            file_content = f.read()

        # Upload no Supabase com header correto
        supabase.storage.from_("shayajean-docs").upload(
            filename,
            file_content,
            {
                "content-type": "application/pdf"
            }
        )

        # Geração da URL pública
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/shayajean-docs/{filename}"
        print("LOG UPLOAD:", public_url)

        return JSONResponse(content={"url": public_url}, media_type="application/json")

    except Exception as e:
        print("ERRO AO SUBIR:", str(e))
        raise HTTPException(status_code=500, detail="Erro ao subir o arquivo no Supabase")

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

@app.get("/")
def root():
    return {"message": "API operacional"}

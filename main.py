from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fpdf import FPDF
import os
import uuid
from supabase import create_client, Client

app = FastAPI()

# Supabase configs
SUPABASE_URL = "https://eaubrpnwyzmsxxawdlqa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class PDFData(BaseModel):
    title: str
    content: str

@app.post("/generate-pdf")
def generate_pdf(data: PDFData):
    pdf_id = str(uuid.uuid4())
    filename = f"{pdf_id}.pdf"
    filepath = f"/tmp/{filename}"

    try:
        # Gerar PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(190, 10, data.title)
        pdf.multi_cell(190, 10, data.content)
        pdf.output(filepath)

        # 📤 Upload real usando caminho do arquivo
        response = supabase.storage.from_("shayajean-docs").upload(
            path=filename,
            file=filepath,
            file_options={"content-type": "application/pdf", "upsert": True}
        )

        print("Resposta do upload:", response)

        # Verifica se houve erro
        if response.get("error"):
            raise HTTPException(status_code=500, detail=response["error"]["message"])

        public_url = f"{SUPABASE_URL}/storage/v1/object/public/shayajean-docs/{filename}"
        return {"message": "PDF gerado com sucesso!", "url": public_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar ou subir PDF: {str(e)}")

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

@app.get("/")
def root():
    return {"message": "API de geração de PDF ativa e segura!"}


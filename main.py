from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fpdf import FPDF
import os
import uuid
from supabase import create_client, Client

app = FastAPI()

# Supabase credentials
SUPABASE_URL = "https://eaubrpnwyzmsxxawdlqa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # sua chave completa
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class PDFData(BaseModel):
    title: str
    content: str

@app.post("/generate-pdf")
def generate_pdf(data: PDFData):
    try:
        # Nome seguro para o arquivo
        safe_title = data.title.strip().replace(" ", "_").replace("/", "-")
        filename = f"{safe_title}_{uuid.uuid4().hex}.pdf"
        filepath = f"/tmp/{filename}"

        # Gera PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(190, 10, f"{data.title}")
        pdf.multi_cell(190, 10, f"{data.content}")
        pdf.output(filepath)

        # Lê o arquivo
        with open(filepath, "rb") as f:
            file_data = f.read()

        # Força upload
        result = supabase.storage.from_("shayajean-docs").upload(
            path=filename,
            file=file_data,
            file_options={"content-type": "application/pdf", "upsert": True}
        )

        print("LOG UPLOAD:", result)

        # Valida erro explícito
        if result.get("error"):
            raise Exception(result["error"]["message"])

        # Link final
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/shayajean-docs/{filename}"
        return {"message": "PDF gerado com sucesso!", "url": public_url}

    except Exception as e:
        print("ERRO:", e)
        raise HTTPException(status_code=500, detail=f"Erro ao gerar ou subir o PDF: {str(e)}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

@app.get("/")
def root():
    return {"message": "API operacional"}

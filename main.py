from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fpdf import FPDF
import os
import uuid
from supabase import create_client, Client

app = FastAPI()

# Supabase configs
SUPABASE_URL = "https://eaubrpnwyzmsxxawdlqa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVhdWJycG53eXptc3h4YXdkbHFhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5MjIzMTIsImV4cCI6MjA2MDQ5ODMxMn0.zz5kWKbTpzFfjq-iw_awaLdlVjG_NuiZWh_fvaprC2A"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class PDFData(BaseModel):
    title: str
    content: str

@app.post("/generate-pdf")
def generate_pdf(data: PDFData):
    filename = f"{uuid.uuid4()}.pdf"
    filepath = f"/tmp/{filename}"  # Render exige uso de /tmp

    try:
        # Gerar PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(190, 10, f"{data.title}")
        pdf.multi_cell(190, 10, f"{data.content}")
        pdf.output(filepath)

        # Upload para Supabase
        with open(filepath, "rb") as f:
            file_content = f.read()
            response = supabase.storage.from_("shayajean-docs").upload(
                path=filename,
                file=file_content,
                file_options={"content-type": "application/pdf", "upsert": True}
            )

        # Log de resposta
        print("Supabase upload response:", response)

        # Verificar erro no upload
        if "error" in response and response["error"]:
            raise HTTPException(status_code=500, detail=response["error"]["message"])

        public_url = f"{SUPABASE_URL}/storage/v1/object/public/shayajean-docs/{filename}"
        return {"url": public_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

@app.get("/")
def root():
    return {"message": "API de geração de PDF ativa e funcional!"}



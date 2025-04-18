from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fpdf import FPDF
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from datetime import datetime
import os

app = FastAPI()

# Supabase configs
SUPABASE_URL = "https://qqfsdibkhzonymwcttjj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFxZnNkaWJraHpvbnltd2N0dGpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5Mjc5MTksImV4cCI6MjA2MDUwMzkxOX0.rRwwa8w_MLD_eVHkqsMw2hpIPj_uqxSln1EACuMf4vo"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class PDFData(BaseModel):
    title: str
    content: str

@app.post("/generate-pdf")
async def generate_pdf(request: Request):
    body = await request.json()

    title = body.get("title", "PDF Sem Título")
    content = body.get("content")

    if not content:
        raise HTTPException(status_code=400, detail="Campo 'content' é obrigatório.")

    filename = f"{title.replace(' ', '_')}_{int(datetime.now().timestamp())}.pdf"
    filepath = f"/tmp/{filename}"

    try:
        pdf = FPDF()
        pdf.add_page()

        try:
            font_path = os.path.join(os.path.dirname(__file__), "fonts/NotoColorEmoji.ttf")
            if os.path.exists(font_path):
                pdf.add_font("Emoji", "", font_path, uni=True)
                pdf.set_font("Emoji", size=12)
            else:
                pdf.set_font("Arial", size=12)

            title = title if isinstance(title, str) else "PDF Sem Título"
            content = content if isinstance(content, str) else ""

            pdf.multi_cell(190, 10, title)
            pdf.ln(5)
            pdf.multi_cell(190, 10, content)
            pdf.output(filepath)

        except Exception as e:
            print("ERRO AO GERAR PDF:", str(e))
            raise HTTPException(status_code=500, detail=f"Erro ao gerar o PDF: {str(e)}")

        with open(filepath, "rb") as f:
            file_content = f.read()

        try:
            supabase.storage.from_("shayajean-docs").upload(
                filename,
                file_content,
                {
                    "content-type": "application/pdf"
                }
            )
        except Exception as e:
            print("ERRO NO UPLOAD:", str(e))
            raise HTTPException(status_code=500, detail=f"Erro ao subir o arquivo no Supabase: {str(e)}")

        public_url = f"{SUPABASE_URL}/storage/v1/object/public/shayajean-docs/{filename}"
        print("LOG UPLOAD:", public_url)

        return JSONResponse(content={"url": public_url}, media_type="application/json")

    except Exception as e:
        print("ERRO GERAL:", str(e))
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

@app.get("/")
def root():
    return {"message": "API operacional"}

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fpdf import FPDF
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from datetime import datetime
import os
import re

# Certifique-se de que o pacote fpdf2 esteja instalado corretamente
# Execute no terminal: pip install fpdf2

app = FastAPI()

# Supabase configs
SUPABASE_URL = "https://qqfsdibkhzonymwcttjj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFxZnNkaWJraHpvbnltd2N0dGpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5Mjc5MTksImV4cCI6MjA2MDUwMzkxOX0.rRwwa8w_MLD_eVHkqsMw2hpIPj_uqxSln1EACuMf4vo"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class PDFData(BaseModel):
    title: str
    content: str

def contains_emoji(text):
    emoji_pattern = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+", flags=re.UNICODE)
    return bool(emoji_pattern.search(text))

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

        font_path_emoji = os.path.join(os.path.dirname(__file__), "fonts/NotoColorEmoji.ttf")
        has_emoji_font = os.path.exists(font_path_emoji)

        if has_emoji_font:
            pdf.add_font("NotoColorEmoji", "", font_path_emoji, uni=True)

        pdf.set_font("Arial", size=12)

        def write_mixed_text(text):
            emoji_pattern = re.compile("([\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF])", flags=re.UNICODE)
            parts = emoji_pattern.split(text)
            for part in parts:
                if contains_emoji(part) and has_emoji_font:
                    pdf.set_font("NotoColorEmoji", size=12)
                else:
                    pdf.set_font("Arial", size=12)
                pdf.write(10, part)
            pdf.ln(10)

        pdf.set_font("Arial", size=14)
        pdf.cell(0, 10, title, ln=True)
        pdf.ln(5)

        for line in content.split('\n'):
            write_mixed_text(line)

        pdf.output(filepath)

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

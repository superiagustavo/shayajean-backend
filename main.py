from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fpdf import FPDF
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from datetime import datetime
import os
import re
import unicodedata

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
        pdf.set_auto_page_break(auto=True, margin=15)

        font_path_emoji = os.path.join(os.path.dirname(__file__), "fonts/seguiemj-1.35-flat.ttf")
        font_path_text = os.path.join(os.path.dirname(__file__), "fonts/DejaVuSans.ttf")

        if os.path.exists(font_path_emoji) and os.path.exists(font_path_text):
            pdf.add_font("SegoeEmoji", "", font_path_emoji, uni=True)
            pdf.add_font("TextFont", "", font_path_text, uni=True)
        else:
            raise HTTPException(status_code=500, detail="Fonte necessária não encontrada.")

        def is_emoji(char):
            return ord(char) >= 0x1F300 and ord(char) <= 0x1FAFF

        pdf.set_font("TextFont", size=14)
        pdf.multi_cell(0, 10, title)
        pdf.ln(5)

        max_width = 180
        for line in content.split('\n'):
            buffer = ""
            current_font = "TextFont"
            for char in line:
                font = "SegoeEmoji" if is_emoji(char) else "TextFont"
                if font != current_font:
                    if buffer:
                        pdf.set_font(current_font, size=12)
                        pdf.multi_cell(0, 10, buffer)
                        buffer = ""
                    current_font = font
                if pdf.get_string_width(buffer + char) > max_width:
                    pdf.set_font(current_font, size=12)
                    pdf.multi_cell(0, 10, buffer)
                    buffer = char
                else:
                    buffer += char
            if buffer:
                pdf.set_font(current_font, size=12)
                pdf.multi_cell(0, 10, buffer)

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

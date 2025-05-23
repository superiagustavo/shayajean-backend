from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fpdf import FPDF
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from datetime import datetime
import os
import re
import unicodedata

app = FastAPI()

# Use variáveis de ambiente para segurança
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class PDFData(BaseModel):
    title: str
    content: str

def remove_emojis(text):
    emoji_pattern = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+", flags=re.UNICODE)
    return emoji_pattern.sub(r"", text)

def remove_accents(text):
    nfkd_form = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

@app.post("/generate-pdf")
async def generate_pdf(data: PDFData):
    title = data.title or "PDF Sem Título"
    content = data.content

    if not content:
        raise HTTPException(status_code=400, detail="Campo 'content' é obrigatório.")

    clean_title = remove_accents(remove_emojis(title))
    filename = f"{clean_title.replace(' ', '_')}_{int(datetime.now().timestamp())}.pdf"
    filepath = f"/tmp/{filename}"

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        font_path_text = os.path.join(os.path.dirname(__file__), "fonts/DejaVuSans.ttf")

        if os.path.exists(font_path_text):
            pdf.add_font("TextFont", "", font_path_text, uni=True)
            pdf.add_font("TextFont", "B", font_path_text, uni=True)
            pdf.set_font("TextFont", size=13)
        else:
            # Fallback para fonte padrão se não encontrar DejaVuSans.ttf
            pdf.set_font("Helvetica", size=13)

        aviso = "⚠️ Neste momento, os PDFs estão sendo gerados apenas com texto, sem os emojis."
        pdf.set_font("TextFont", size=10)
        pdf.multi_cell(0, 10, aviso)
        pdf.ln(5)

        pdf.set_font("TextFont", style="B", size=14)
        pdf.multi_cell(0, 10, clean_title)
        pdf.ln(5)

        pdf.set_font("TextFont", size=13)
        max_width = pdf.w - 2 * pdf.l_margin

        # Limpeza completa do conteúdo
        clean_content = re.sub(r'[^\x20-\x7E\u00A0-\u017F\u0180-\u024F\s]', '', remove_emojis(content))
        clean_content = re.sub(r'[\u200b\u200e\u202a-\u202e]', '', clean_content)

        for line in clean_content.split('\n'):
            buffer = ""
            for char in line:
                char_width = pdf.get_string_width(char)
                total_width = pdf.get_string_width(buffer + char)
                if char_width == 0 or char_width != char_width:
                    continue
                if char_width > max_width:
                    pdf.multi_cell(0, 10, char)
                    buffer = ""
                elif total_width > max_width:
                    pdf.multi_cell(0, 10, buffer)
                    buffer = char
                else:
                    buffer += char
            if buffer:
                pdf.multi_cell(0, 10, buffer)

        pdf.output(filepath)

        with open(filepath, "rb") as f:
            file_content = f.read()

        try:
            supabase.storage.from_("shayajean-docs").upload(
                path=filename,
                file=file_content,
                file_options={
                    "content-type": "application/pdf"
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao subir o arquivo no Supabase: {str(e)}")

        public_url = f"{SUPABASE_URL}/storage/v1/object/public/shayajean-docs/{filename}"
        return JSONResponse(content={
            "url": public_url,
            "mensagem": "PDF gerado com sucesso. Neste momento, os emojis foram removidos e o conteúdo está formatado apenas com texto."
        }, media_type="application/json")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

@app.get("/")
def root():
    return {"message": "API operacional"}

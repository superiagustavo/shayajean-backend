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

    # Nome do arquivo com timestamp para evitar sobrescrita
    filename = f"{title.replace(' ', '_')}_{int(datetime.now().timestamp())}.pdf"
    filepath = f"/tmp/{filename}"

    pdf = FPDF()
    pdf.add_page()

try:
    if os.path.exists("DejaVuSans.ttf"):
        pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        pdf.set_font("DejaVu", size=12)
    else:
        pdf.set_font("Arial", size=12)

    # Só adiciona texto depois que a fonte estiver definida
    pdf.multi_cell(190, 10, title)
    pdf.multi_cell(190, 10, content)
    pdf.output(filepath)

except Exception as e:
    print("ERRO AO GERAR PDF:", str(e))
    raise HTTPException(status_code=500, detail="Erro ao gerar o PDF")

        # Leitura do conteúdo do arquivo
        with open(filepath, "rb") as f:
            file_content = f.read()

        # Upload no Supabase
        supabase.storage.from_("shayajean-docs").upload(
            filename,
            file_content,
            {
                "content-type": "application/pdf"
            }
        )

        # Link público
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

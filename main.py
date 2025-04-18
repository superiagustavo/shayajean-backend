from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class PDFData(BaseModel):
    title: str
    content: str

@app.post("/generate-pdf")
def generate_pdf(data: PDFData):
    return {
        "status": "✅ ação chegou no backend!",
        "dados_recebidos": {
            "title": data.title,
            "content": data.content
        }
    }

@app.get("/")
def root():
    return {"message": "API de teste ativa"}

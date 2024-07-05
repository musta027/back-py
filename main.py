from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from fpdf import FPDF
import openai
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://epitet.vercel.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

if not openai.api_key:
    raise HTTPException(status_code=500, detail="OpenAI API key is not set")

class DocumentRequest(BaseModel):
    user_input: str

class PDF(FPDF):
    def header(self):
        self.add_font('DejaVu', '', './fonts/DejaVuSans.ttf', uni=True)
        self.set_font('DejaVu', '', 12)
        self.cell(0, 10, 'tezDet.ai', 0, 1, 'C')

    def chapter_body(self, body):
        self.set_font('DejaVu', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

@app.post("/generate_document/")
async def generate_document(request: DocumentRequest):
    try:
        # Использование OpenAI API для генерации текста документа
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a personal lawyer, attorney, notary, accountant, secretary, office manager, administrative staff, HR specialist, and contract manager. Your job is to quickly, accurately, safely, and error-free fill out necessary documents, forms, and so on. Generate only the main content of the document without any additional notes or warnings."},
                {"role": "user", "content": f"На основе следующих данных: {request.user_input}, составь основной текст документа. Не включай никакие предупреждения, примечания или лишние объяснения."}
            ],
            max_tokens=1000
        )
        document_text = response['choices'][0]['message']['content'].strip()

        # Создание PDF документа
        pdf = PDF(format='A4')
        pdf.add_page()
        pdf.chapter_body(document_text)

        # Сохранение PDF в файл
        pdf_file = "/tmp/generated_document.pdf"
        pdf.output(pdf_file)

        # Чтение PDF файла и возврат в виде Response
        with open(pdf_file, "rb") as f:
            pdf_data = f.read()

        return Response(content=pdf_data, media_type="application/pdf", headers={
            "Content-Disposition": "attachment; filename=generated_document.pdf"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to the Document Generation API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

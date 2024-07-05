from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from fpdf import FPDF
import openai
import os
from dotenv import load_dotenv

app = FastAPI()

# Загрузка переменных окружения из .env файла
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise HTTPException(status_code=500, detail="OpenAI API key is not set")

class DocumentRequest(BaseModel):
    document_type: str
    user_input: str

class PDF(FPDF):
    def header(self):
        self.add_font('DejaVu', '', './fonts/DejaVuSans.ttf', uni=True)
        self.set_font('DejaVu', '', 12)
        self.cell(0, 10, 'Официальный документ', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('DejaVu', '', 12)
        self.cell(0, 10, title, 0, 1, 'L')

    def chapter_body(self, body):
        self.set_font('DejaVu', '', 12)
        self.multi_cell(0, 10, body)

@app.post("/generate_document/")
async def generate_document(request: DocumentRequest):
    try:
        # Использование OpenAI API для генерации текста документа
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Создай официальный документ типа {request.document_type} на основе следующих данных: {request.user_input}"}
            ],
            max_tokens=1000
        )
        document_text = response['choices'][0]['message']['content'].strip()

        # Создание PDF документа
        pdf = PDF()
        pdf.add_page()
        pdf.chapter_title(f"Тип документа: {request.document_type}")
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

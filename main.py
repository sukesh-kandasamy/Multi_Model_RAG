# 1. Install required packages
# !pip install fastapi uvicorn pyngrok nest_asyncio

import uvicorn
from fastapi import FastAPI, Request, File, UploadFile, Body
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pyngrok import ngrok
import shutil
import os
from rag_connector import run_complete_ingestion_pipeline, generate_final_answer
from dotenv import load_dotenv

load_dotenv()



#Config
app = FastAPI()
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")
ngrok.set_auth_token(NGROK_AUTH_TOKEN)
templates = Jinja2Templates(directory="templates")

current_path = ""
UPLOAD_DIR = "uploads"


db=""

@app.get("/")
async def main_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def handle_upload(request: Request, file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return JSONResponse(
            status_code=400, 
            content={"status": "error", "message": "Only PDF files are allowed."}
        )
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # RETURN JSON INSTEAD OF TEMPLATE
        result = run_complete_ingestion_pipeline(file_path)
        if result['status']:
          global db
          db = result['db']
          return {
              "status": "success",
              "message": f"uploaded successfully and processes successfully",
              "filename": file.filename
          }
        else:
           return {
              "status": "success",
              "message": f"uploaded successfully and processed failed",
              "filename": file.filename
          }

    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"status": "error", "message": str(e)}
        )


@app.post("/chat")
async def chat(data: dict = Body(...)):
    user_text = data.get("message", "")
    bot_response = generate_final_answer(db, user_text)
    
    return {"response": bot_response}

try:
    public_url = ngrok.connect(8000)
    print(f"\n🚀 PUBLIC URL: {public_url}")
    print("Click the link above to access your API!\n")
except Exception as e:
    print(f"Error connecting ngrok: {e}")

# Run the server
if __name__ == "__main__":
    # Pass the string "main:app" instead of the variable app
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
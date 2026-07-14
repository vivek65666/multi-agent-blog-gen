import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from graph import app_graph

load_dotenv()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # FIXED: Passing request as the first argument
    return templates.TemplateResponse(
        request, 
        "index.html", 
        {"draft": None, "topic": ""}
    )

@app.post("/generate", response_class=HTMLResponse)
async def generate_blog(request: Request, topic: str = Form(...)):
    initial_state = {
        "topic": topic,
        "research_notes": "",
        "draft": "",
        "feedback": "",
        "revision_count": 0,
        "approved": False
    }
    
    # Run the multi-agent graph loop
    final_output = app_graph.invoke(initial_state)
    
    # FIXED: Passing request as the first argument
    return templates.TemplateResponse(
        request, 
        "index.html", 
        {"draft": final_output["draft"], "topic": topic}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
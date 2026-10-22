import logging

import nh3
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from graph import get_graph
from state import initial_state

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("blog_app")

app = FastAPI(title="Multi-Agent Blog Generator")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# The LLM writes HTML, so sanitize it before rendering with `| safe`.
ALLOWED_TAGS = {"div", "h1", "h2", "h3", "h4", "p", "ul", "ol", "li", "strong", "em", "b", "i",
                "a", "blockquote", "code", "pre", "br", "span"}


def render(request: Request, **context):
    base = {"draft": None, "topic": "", "error": None, "meta": None}
    base.update(context)
    return templates.TemplateResponse(request, "index.html", base)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return render(request)


@app.post("/generate", response_class=HTMLResponse)
async def generate_blog(request: Request, topic: str = Form(..., max_length=200)):
    topic = topic.strip()
    if not topic:
        return render(request, error="Please enter a topic.")
    try:
        # graph.invoke is blocking; keep the event loop free.
        result = await run_in_threadpool(get_graph().invoke, initial_state(topic))
    except Exception:
        logger.exception("Blog generation failed")
        return render(request, topic=topic, error="Generation failed. Check your API keys and try again.")

    clean_html = nh3.clean(result["draft"], tags=ALLOWED_TAGS, attributes={"a": {"href"}})
    meta = {
        "revisions": result["revision_count"],
        "score": result["score"],
        "approved": result["approved"],
        "sources": result["sources"],
    }
    return render(request, draft=clean_html, topic=topic, meta=meta)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

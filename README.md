# Multi-Agent Blog Generator Engine 🚀

An autonomous content generation platform powered by an advanced LangGraph multi-agent swarm. The system orchestrates specialized AI agents to discover data, scrape targets, compose copy, and evaluate final production quality using stateful, self-correcting cyclic graph routing.

## 🛠️ Architecture Blueprint
- **Search & Scraper Agent (Researcher Node):** Dynamically calls the Tavily API to browse the live web, gather context snippets, and assemble unified research notes.
- **Copywriter Agent (Writer Node):** Generates structural, SEO-optimized content formatted inside target HTML blocks without structural syntax leaking.
- **Editor-in-Chief Agent (Editor Node):** Evaluates drafts against professional guidelines, issuing an `APPROVED` signal or feeding custom revision notes back to the graph loop.

## 🧰 Tech Stack
- **Frameworks:** LangGraph, LangChain, FastAPI, Uvicorn
- **LLM Engine:** Gemini API (`gemini-3.1-flash-lite`, `gemini-3.5-flash`)
- **Tools:** Tavily Search Engine, Python 3.x
- **Frontend:** Responsive HTML5 / CSS3

  ## 🖥️ Application Interface & Workflow

### 1. Landing Page (Ready for Swarm Deployment)
![Landing Page](./1.png)

### 2. Final Reviewed Output (After Agent Swarm Orchestration)
![Final Output](./2.png)

## 🚀 Local Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/vivek65666/multi-agent-blog-gen.git](https://github.com/vivek65666/multi-agent-blog-gen.git)
   cd multi-agent-blog-gen

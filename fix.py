import os

# Create folders if they don't exist
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)

# Clean UTF-8 HTML structure
html_code = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Agent Blog Gen Platform</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Autonomous Content Agent Swarm</h1>
            <p class="subtitle">Powered by LangGraph Workflow Orchestration</p>
        </header>
        
        <div class="form-box">
            <form action="/generate" method="POST">
                <div class="form-group">
                    <input type="text" name="topic" placeholder="Enter a technical blog topic..." required>
                    <button type="submit">Deploy Swarm Engine</button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>"""

# Clean UTF-8 CSS structure
css_code = """body { font-family: sans-serif; background: #f8fafc; padding: 3rem 1rem; text-align: center; }"""

# Write files using Python's reliable UTF-8 encoder
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html_code)

with open('static/style.css', 'w', encoding='utf-8') as f:
    f.write(css_code)

print("SUCCESS: Frontend files rewritten cleanly in UTF-8!")
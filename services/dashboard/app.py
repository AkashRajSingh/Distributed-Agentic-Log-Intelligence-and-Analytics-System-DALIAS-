
"""Tiny Flask dashboard with endpoints to view logs and request agent analysis."""
import os
from flask import Flask, render_template_string, request, jsonify
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import threading
import requests

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://mongo:27017')
AGENT_HOST = os.environ.get('AGENT_HOST', 'agent')

app = Flask(__name__)
client = AsyncIOMotorClient(MONGO_URI)
db = client.dalias
collection = db.processed_logs

INDEX_HTML = """
<!doctype html>
<title>DALIAS Dashboard</title>
<h1>DALIAS - Recent Logs</h1>
<button onclick="runAnalysis()">Run AI Analysis</button>
<pre id="analysis">(analysis output will appear here)</pre>
<ul id="logs">
{% for l in logs %}
  <li>[{{l.timestamp}}] [{{l.service}}] [{{l.level}}] {{l.message}} {% if l.anomaly %}<strong>(ANOMALY)</strong>{% endif %}</li>
{% endfor %}
</ul>
<script>
async function runAnalysis(){
  document.getElementById('analysis').innerText = 'Running...';
  const resp = await fetch('/analyze');
  const txt = await resp.text();
  document.getElementById('analysis').innerText = txt;
}
</script>
"""

@app.route('/')
def index():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logs = loop.run_until_complete(collection.find().sort([('_id', -1)]).limit(50).to_list(50))
    # convert keys
    for l in logs:
        l['timestamp'] = l.get('timestamp', '')
        l['service'] = l.get('service', '')
        l['level'] = l.get('level', '')
        l['message'] = l.get('message', '')
    return render_template_string(INDEX_HTML, logs=logs)

@app.route('/analyze')
def analyze():
    # call agent container via docker network (here we simply run the agent script using its container command)
    # For simplicity, call agent via docker exec is not possible from container; instead, call agent HTTP endpoint if implemented.
    # We kept agent as CLI that prints analysis. For this minimal system, we'll call the agent microservice by invoking its Python file via subprocess.
    import subprocess
    try:
        out = subprocess.check_output(['python', '/app/../agent/agent.py'], stderr=subprocess.STDOUT, timeout=60)
        return out.decode('utf-8')
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)



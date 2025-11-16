"""Tiny Flask dashboard with endpoints to view logs and request agent analysis."""
import os
from flask import Flask, render_template_string, request, jsonify
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://mongo:27017')
AGENT_URL = os.environ.get('AGENT_URL', 'http://agent:5000/analyze')

app = Flask(__name__)
client = AsyncIOMotorClient(MONGO_URI)
db = client.dalias
collection = db.processed_logs

INDEX_HTML = """
<!doctype html>
<html>
<head>
    <title>DALIAS Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
        #analysis { background: #f5f5f5; padding: 15px; margin: 20px 0; border: 1px solid #ddd; }
        .error { color: red; }
        .log-item { padding: 5px; border-bottom: 1px solid #eee; }
        .anomaly { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <h1>DALIAS - Recent Logs</h1>
    <button onclick="runAnalysis()">Run AI Analysis</button>
    <pre id="analysis">(analysis output will appear here)</pre>
    <h2>Recent Logs ({{ logs|length }})</h2>
    <div id="logs">
    {% if logs %}
        {% for l in logs %}
        <div class="log-item">
            [{{l.timestamp}}] [{{l.service}}] [{{l.level}}] {{l.message}} 
            {% if l.anomaly %}<span class="anomaly">(ANOMALY)</span>{% endif %}
        </div>
        {% endfor %}
    {% else %}
        <p>No logs available yet.</p>
    {% endif %}
    </div>
    <script>
    async function runAnalysis(){
        const analysisEl = document.getElementById('analysis');
        analysisEl.innerText = 'Running analysis...';
        analysisEl.className = '';
        try {
            const resp = await fetch('/analyze');
            if (!resp.ok) {
                throw new Error(`HTTP error! status: ${resp.status}`);
            }
            const txt = await resp.text();
            analysisEl.innerText = txt;
        } catch(e) {
            analysisEl.innerText = 'Error: ' + e.message;
            analysisEl.className = 'error';
            console.error('Analysis error:', e);
        }
    }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    try:
        logger.info("Dashboard index route accessed")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info("Fetching logs from MongoDB...")
        logs = loop.run_until_complete(
            collection.find().sort([('_id', -1)]).limit(50).to_list(50)
        )
        logger.info(f"Retrieved {len(logs)} logs")
        
        # Convert MongoDB documents to display format
        for l in logs:
            l['timestamp'] = l.get('timestamp', 'N/A')
            l['service'] = l.get('service', 'unknown')
            l['level'] = l.get('level', 'info')
            l['message'] = l.get('message', '')
            l['anomaly'] = l.get('anomaly', False)
        
        return render_template_string(INDEX_HTML, logs=logs)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}", exc_info=True)
        return f"<h1>Error</h1><pre>{str(e)}</pre>", 500

@app.route('/analyze')
def analyze():
    """Call agent service to run analysis."""
    try:
        logger.info(f"Calling agent at {AGENT_URL}")
        response = requests.get(AGENT_URL, timeout=60)
        response.raise_for_status()
        logger.info("Agent analysis completed successfully")
        return response.text
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Cannot connect to agent service: {str(e)}")
        return f"Cannot connect to agent service. Is it running?", 503
    except requests.exceptions.Timeout as e:
        logger.error(f"Agent request timed out: {str(e)}")
        return f"Agent analysis timed out", 504
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        return f"Analysis failed: {str(e)}", 500

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    logger.info(f"Starting dashboard on port 8000")
    logger.info(f"MongoDB URI: {MONGO_URI}")
    logger.info(f"Agent URL: {AGENT_URL}")
    app.run(host='0.0.0.0', port=8000, debug=True)
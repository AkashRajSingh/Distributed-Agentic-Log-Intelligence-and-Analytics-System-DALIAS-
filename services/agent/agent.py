
"""Agent service that reads recent logs from Mongo and uses Gemini to generate a human-readable analysis."""
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import google.generativeai as genai

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://mongo:27017')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
client = AsyncIOMotorClient(MONGO_URI)
db = client.dalias
collection = db.processed_logs

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

async def fetch_recent(n=100):
    cursor = collection.find().sort([('_id', -1)]).limit(n)
    docs = []
    async for d in cursor:
        d.pop('_id', None)
        docs.append(d)
    return docs

async def generate_analysis(logs):
    # build a short prompt with logs
    snippet = ''
    for l in logs[:30]:
        snippet += f"[{l.get('timestamp')}][{l.get('service')}][{l.get('level')}] {l.get('message')}\\n"
    prompt = (
        "You are a system reliability assistant. Given the following recent logs, provide:\n"
        "1) Short system health summary (1-2 sentences).\n"
        "2) List of likely root causes (3 items).\n"
        "3) Suggested immediate remediation steps (3 items).\n\n"
        "Logs:\n" + snippet
    )
    response = openai.ChatCompletion.create(
        model='gpt-4o',
        messages=[{'role':'user','content':prompt}],
        max_tokens=400
    )
    return response['choices'][0]['message']['content']

async def run_once_and_exit():
    logs = await fetch_recent(100)
    if not logs:
        print('No logs to analyze')
        return
    analysis = await generate_analysis(logs)
    print('=== ANALYSIS START ===')
    print(analysis)
    print('=== ANALYSIS END ===')

if __name__ == '__main__':
    asyncio.run(run_once_and_exit())


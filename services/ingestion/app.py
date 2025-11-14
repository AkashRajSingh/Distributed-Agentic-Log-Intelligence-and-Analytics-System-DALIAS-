"""FastAPI ingestion service that accepts log POSTs and pushes them to Kafka."""
import asyncio
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, Request
import uvicorn
import json
import os

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
TOPIC = "dalias-logs"

app = FastAPI()
producer = None

@app.on_event("startup")
async def startup_event():
    global producer
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKER)
    await producer.start()

@app.on_event("shutdown")
async def shutdown_event():
    await producer.stop()

@app.post("/ingest")
async def ingest(request: Request):
    data = await request.json()
    await producer.send_and_wait(TOPIC, json.dumps(data).encode("utf-8"))
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)

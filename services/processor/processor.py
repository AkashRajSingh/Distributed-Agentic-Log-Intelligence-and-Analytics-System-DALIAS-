"""Simple Kafka consumer that parses logs, detects anomalies, and stores into MongoDB."""
import os
import asyncio
import json
from aiokafka import AIOKafkaConsumer
from motor.motor_asyncio import AsyncIOMotorClient

KAFKA_BOOTSTRAP = os.environ.get('KAFKA_BOOTSTRAP', 'redpanda:9092')
LOG_TOPIC = os.environ.get('LOG_TOPIC', 'raw-logs')
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://mongo:27017')
PROCESSED_COLLECTION = os.environ.get('PROCESSED_COLLECTION', 'processed_logs')

client = AsyncIOMotorClient(MONGO_URI)
db = client.dalias
collection = db[PROCESSED_COLLECTION]

async def is_anomaly(log_obj):
    # naive rules-based anomaly detection
    level = log_obj.get('level','').lower()
    message = log_obj.get('message','')
    if level in ('error','critical'):
        return True
    if 'exception' in message.lower():
        return True
    # latency pattern
    meta = log_obj.get('metadata',{})
    if isinstance(meta, dict):
        if meta.get('latency_ms') and meta['latency_ms'] > 1000:
            return True
    return False

async def process_loop():
    consumer = AIOKafkaConsumer(
        LOG_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id='processor-group',
        auto_offset_reset='earliest'
    )
    await consumer.start()
    try:
        async for msg in consumer:
            try:
                obj = json.loads(msg.value.decode('utf-8'))
            except Exception:
                continue
            obj['_id'] = None
            obj['anomaly'] = await is_anomaly(obj)
            await collection.insert_one(obj)
    finally:
        await consumer.stop()

if __name__ == '__main__':
    asyncio.run(process_loop())


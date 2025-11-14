"""Simple log generator: emits logs by calling ingestion endpoint repeatedly."""
import os
import time
import random
import requests

INGEST_URL = os.environ.get('INGEST_URL', 'http://ingestion:9000/ingest')
SERVICES = ['auth', 'payments', 'orders', 'search', 'worker']
LEVELS = ['info', 'warning', 'error']

messages = [
    'user login successful',
    'payment processed',
    'order created',
    'search index refreshed',
    'background job failed with exception',
    'db connection timeout',
    'cache miss for key',
]

while True:
    payload = {
        'service': random.choice(SERVICES),
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'level': random.choices(LEVELS, weights=[80,15,5])[0],
        'message': random.choice(messages),
        'metadata': {'latency_ms': random.randint(10, 2000)}
    }
    try:
        requests.post(INGEST_URL, json=payload, timeout=3)
    except Exception as e:
        print('failed to send', e)
    time.sleep(0.7)



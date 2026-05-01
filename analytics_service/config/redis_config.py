
from redis.asyncio import Redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
IDEMPOTENCY_TTL = 86400

redis_client = Redis(
    host=REDIS_HOST, 
    port=REDIS_PORT, 
    decode_responses=True,
    max_connections=50,
    socket_timeout=5
)

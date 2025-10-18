from taskiq import TaskiqScheduler
from taskiq_redis import ListQueueBroker
from app.core.config import REDIS_URL

if not REDIS_URL:
    raise ValueError("REDIS_URL environment variable is not set")

broker = ListQueueBroker(REDIS_URL)
scheduler = TaskiqScheduler(broker=broker, sources=[])

@broker.task
async def process_candidate(candidate_id: str):
    print(f"Processing candidate {candidate_id}")

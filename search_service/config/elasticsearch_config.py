from elasticsearch import Elasticsearch, AsyncElasticsearch
import os

ES_HOST = os.getenv("ELASTICSEARCH_HOST")
ES_USER = str(os.getenv("ES_USER", "elastic"))
ES_PASS = str(os.getenv("ES_PASSWORD"))

ES_CONFIG = {
    "hosts": [ES_HOST],
    "basic_auth":(ES_USER, ES_PASS),
    "verify_certs":False,
    "ssl_show_warn":False
}

# Sync Client for the Kafka Consumer
def get_sync_elasticsearch_client():
    if not ES_HOST or ES_HOST == "None" or not ES_PASS:
        raise ValueError("ELASTICSEARCH_HOST is not set. Check your .env file.")
    
    return Elasticsearch(
        **ES_CONFIG
    )

# Async Client for the FastAPI Search API
es_client = AsyncElasticsearch(
    **ES_CONFIG,
    request_timeout=30,
    max_retries=3,
    retry_on_timeout=True
)

async def get_async_elasticsearch_client() -> AsyncElasticsearch:
    return es_client
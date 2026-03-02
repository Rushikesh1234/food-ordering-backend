from elasticsearch import AsyncElasticsearch
import os

ES_HOST = os.getenv("ELASTICSEARCH_HOST")
ES_USER = str(os.getenv("ES_USER", "elastic"))
ES_PASS = str(os.getenv("ES_PASSWORD"))

es_client = AsyncElasticsearch(
    ES_HOST,
    basic_auth=(ES_USER, ES_PASS),
    verify_certs=False,
    ssl_show_warn=False,
    request_timeout=30,
    max_retries=3,
    retry_on_timeout=True
)

async def get_elasticsearch_client() -> AsyncElasticsearch:
    return es_client
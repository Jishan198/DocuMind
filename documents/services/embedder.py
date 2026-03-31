import time
from google import genai
from google.genai import types
from django.conf import settings


class EmbeddingService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model = "models/gemini-embedding-001"
        self.batch_size = 20

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            try:
                result = self.client.models.embed_content(
                    model=self.model,
                    contents=batch,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                )
                all_embeddings.extend([e.values for e in result.embeddings])
            except Exception as e:
                time.sleep(5)
                result = self.client.models.embed_content(
                    model=self.model,
                    contents=batch,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                )
                all_embeddings.extend([e.values for e in result.embeddings])
        return all_embeddings

    def embed_query(self, query: str) -> list[float]:
        result = self.client.models.embed_content(
            model=self.model,
            contents=query,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        return result.embeddings[0].values
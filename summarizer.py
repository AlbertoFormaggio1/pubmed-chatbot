from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline

class Summarizer:
    def __init__(self, embedding_model_name, summarizer_model_name):
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.summarizer = pipeline("summarization", model=summarizer_model_name)

    def find_article(self, articles, user_query):
        article_names = list(articles.keys())
        # Compute embeddings for article titles and the user query
        articles_embeddings = self.embedding_model.encode(article_names)
        query_embedding = self.embedding_model.encode([user_query])
        # Compute the cosine similarity
        similarities = cosine_similarity(articles_embeddings, query_embedding).reshape(-1)
        # Retrieve the article with the highest cosine similarity to the user query
        best_match_idx = similarities.argmax().item()
        matched_article = articles[article_names[best_match_idx]]

        return matched_article
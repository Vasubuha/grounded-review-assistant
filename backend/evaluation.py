from langchain_huggingface import HuggingFaceEndpointEmbeddings
from core.config import settings
import numpy as np
import warnings

warnings.filterwarnings("ignore")

embeddings_model = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2",
    huggingfacehub_api_token=settings.HF_TOKEN
)

def cosine_similarity(vec_a, vec_b):
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    return dot_product / (norm_a * norm_b)

def evaluate_retrieval(ground_truth_query: str, retrieved_texts: list[str]) -> float:
    """
    Evaluates retrieval by calculating the semantic similarity between the original 
    query intent and the retrieved texts. Returns the average similarity score.
    """
    if not retrieved_texts:
        return 0.0
        
    query_vector = embeddings_model.embed_query(ground_truth_query)
    
    scores = []
    for text in retrieved_texts:
        text_vector = embeddings_model.embed_query(text)
        sim = cosine_similarity(query_vector, text_vector)
        scores.append(sim)
        
    # We can take the max or average depending on the strictness of evaluation
    return sum(scores) / len(scores)

if __name__ == "__main__":
    # Test evaluation
    query = "The phone heats up significantly during gaming sessions."
    retrieved_good = [
        "Heating issues are very prominent when playing heavy games like Genshin Impact.",
        "Gets warm during extended use."
    ]
    retrieved_bad = [
        "The camera takes great pictures in daylight.",
        "Battery life is 5000mAh."
    ]
    
    score_good = evaluate_retrieval(query, retrieved_good)
    score_bad = evaluate_retrieval(query, retrieved_bad)
    
    print(f"Semantic Eval Score (Relevant Contexts): {score_good:.4f}")
    print(f"Semantic Eval Score (Irrelevant Contexts): {score_bad:.4f}")

from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple


class EmbeddingEngine:
    def __init__(self):
        self.model = None
    
    def _load_model(self):
        """Lazy load the sentence transformer model"""
        if self.model is None:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        self._load_model()
        return self.model.encode(text, convert_to_tensor=False)
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts"""
        self._load_model()
        return self.model.encode(texts, convert_to_tensor=False)
    
    def calculate_cosine_similarity(self, job_embedding: np.ndarray, resume_embeddings: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity between job embedding and resume embeddings"""
        # Reshape job_embedding to 2D array for sklearn compatibility
        job_embedding_2d = job_embedding.reshape(1, -1)
        similarities = cosine_similarity(job_embedding_2d, resume_embeddings)[0]
        return similarities
    
    def rank_candidates(self, job_description: str, resume_texts: List[str], candidate_names: List[str], filenames: List[str]) -> List[Tuple[str, str, float]]:
        """
        Rank candidates based on cosine similarity with job description
        Returns list of (candidate_name, filename, similarity_score) tuples sorted by similarity
        """
        # Generate job description embedding
        job_embedding = self.generate_embedding(job_description)
        
        # Generate resume embeddings
        resume_embeddings = self.generate_embeddings(resume_texts)
        
        # Calculate similarities
        similarities = self.calculate_cosine_similarity(job_embedding, resume_embeddings)
        
        # Create candidate tuples and sort by similarity (descending)
        candidates = list(zip(candidate_names, filenames, similarities))
        candidates.sort(key=lambda x: x[2], reverse=True)
        
        return candidates
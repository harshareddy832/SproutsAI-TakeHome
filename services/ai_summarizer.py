import openai
import os
from typing import Optional


class AISummarizer:
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client if API key is available"""
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            openai.api_key = api_key
            self.client = openai.OpenAI(api_key=api_key)
    
    def generate_summary(self, job_description: str, resume_text: str, candidate_name: str) -> str:
        """
        Generate AI summary explaining why candidate fits the role
        Returns generic message if OpenAI is not available or fails
        """
        if not self.client:
            return "AI summary unavailable - OpenAI API key not configured"
        
        try:
            # Truncate resume text to avoid token limits (keep first 1500 characters)
            resume_excerpt = resume_text[:1500] + "..." if len(resume_text) > 1500 else resume_text
            
            prompt = f"""Based on the job description and resume excerpt below, explain in 2-3 sentences why this candidate fits this role. Focus on matching skills, experience, and qualifications.

Job Description:
{job_description[:1000]}

Resume Excerpt for {candidate_name}:
{resume_excerpt}

Provide a concise explanation of the match:"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert HR assistant. Provide clear, concise explanations of candidate-job fit."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating AI summary: {e}")
            return f"{candidate_name} shows relevant experience and skills that align with the job requirements based on their background and qualifications."
    
    def is_available(self) -> bool:
        """Check if AI summarizer is available (has valid API key)"""
        return self.client is not None
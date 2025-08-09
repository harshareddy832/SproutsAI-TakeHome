from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import requests
import json
import time


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, api_key: str, model: str, custom_endpoint: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.custom_endpoint = custom_endpoint
        self.provider_name = self.__class__.__name__.replace('Provider', '').lower()
    
    @abstractmethod
    def generate_summary(self, job_description: str, resume_text: str, candidate_name: str) -> str:
        """Generate AI summary for candidate fit"""
        pass
    
    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Test API connection and return (success, message)"""
        pass
    
    @abstractmethod
    def get_cost_estimate(self, text_length: int) -> float:
        """Estimate cost for processing given text length"""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider implementation"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", custom_endpoint: Optional[str] = None):
        super().__init__(api_key, model, custom_endpoint)
        self.base_url = custom_endpoint or "https://api.openai.com/v1"
    
    def generate_summary(self, job_description: str, resume_text: str, candidate_name: str) -> str:
        try:
            # Truncate inputs to manage token limits
            job_excerpt = job_description[:1200]
            resume_excerpt = resume_text[:1500]
            
            prompt = f"""You are an expert HR recruiter analyzing candidate fit.

Job Description: {job_excerpt}

Candidate Resume: {resume_excerpt}

Generate a concise 3-sentence analysis explaining:
1. Why this candidate is an excellent fit for this specific role
2. Their strongest matching qualifications 
3. The unique value they would bring to the position

Format as professional recruiter insights, not a generic summary."""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert HR recruiter. Provide specific, professional candidate analysis."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 200,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
            else:
                return f"Error generating summary: {response.status_code}"
                
        except Exception as e:
            return f"Unable to generate AI summary: {str(e)}"
    
    def test_connection(self) -> tuple[bool, str]:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 5
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"API Error: {response.status_code}"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def get_cost_estimate(self, text_length: int) -> float:
        # Rough token estimation (1 token ≈ 4 characters)
        estimated_tokens = text_length // 4
        # GPT-3.5-turbo pricing: ~$0.002 per 1K tokens
        return (estimated_tokens / 1000) * 0.002


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229", custom_endpoint: Optional[str] = None):
        super().__init__(api_key, model, custom_endpoint)
        self.base_url = custom_endpoint or "https://api.anthropic.com/v1"
    
    def generate_summary(self, job_description: str, resume_text: str, candidate_name: str) -> str:
        try:
            job_excerpt = job_description[:1200]
            resume_excerpt = resume_text[:1500]
            
            prompt = f"""As a senior talent acquisition specialist, analyze this candidate's fit:

Position Requirements: {job_excerpt}

Candidate Profile: {resume_excerpt}

Provide 3 specific insights:
- Primary strength alignment with role requirements
- Standout qualifications that differentiate this candidate  
- Potential impact they could make in this position

Keep analysis professional and specific to this role-candidate match."""

            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": self.model,
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['content'][0]['text'].strip()
            else:
                return f"Error generating summary: {response.status_code}"
                
        except Exception as e:
            return f"Unable to generate AI summary: {str(e)}"
    
    def test_connection(self) -> tuple[bool, str]:
        try:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": self.model,
                "max_tokens": 5,
                "messages": [{"role": "user", "content": "Test"}]
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"API Error: {response.status_code}"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def get_cost_estimate(self, text_length: int) -> float:
        estimated_tokens = text_length // 4
        # Claude pricing: ~$0.003 per 1K tokens
        return (estimated_tokens / 1000) * 0.003


class GoogleAIProvider(AIProvider):
    """Google AI Gemini provider implementation"""
    
    def __init__(self, api_key: str, model: str = "gemini-pro", custom_endpoint: Optional[str] = None):
        super().__init__(api_key, model, custom_endpoint)
        self.base_url = custom_endpoint or "https://generativelanguage.googleapis.com/v1"
    
    def generate_summary(self, job_description: str, resume_text: str, candidate_name: str) -> str:
        try:
            job_excerpt = job_description[:1200]
            resume_excerpt = resume_text[:1500]
            
            prompt = f"""Analyze this candidate's fit as an expert recruiter:

Job: {job_excerpt}

Candidate: {resume_excerpt}

Write 3 sentences explaining: 1) Best qualification match 2) Unique strengths 3) Value they'd bring. Be specific and professional."""

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": 200,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(
                f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
            else:
                return f"Error generating summary: {response.status_code}"
                
        except Exception as e:
            return f"Unable to generate AI summary: {str(e)}"
    
    def test_connection(self) -> tuple[bool, str]:
        try:
            payload = {
                "contents": [{"parts": [{"text": "Test"}]}],
                "generationConfig": {"maxOutputTokens": 5}
            }
            
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            
            response = requests.post(
                url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "Connection successful"
            else:
                error_detail = ""
                try:
                    error_data = response.json()
                    error_detail = error_data.get('error', {}).get('message', str(error_data))
                except:
                    error_detail = response.text[:200] if response.text else "No error details"
                
                return False, f"API Error {response.status_code}: {error_detail}"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def get_cost_estimate(self, text_length: int) -> float:
        estimated_tokens = text_length // 4
        # Gemini pricing: ~$0.001 per 1K tokens
        return (estimated_tokens / 1000) * 0.001


class GroqProvider(AIProvider):
    """Groq provider implementation"""
    
    def __init__(self, api_key: str, model: str = "llama3-8b-8192", custom_endpoint: Optional[str] = None):
        super().__init__(api_key, model, custom_endpoint)
        self.base_url = custom_endpoint or "https://api.groq.com/openai/v1"
    
    def generate_summary(self, job_description: str, resume_text: str, candidate_name: str) -> str:
        try:
            job_excerpt = job_description[:1200]
            resume_excerpt = resume_text[:1500]
            
            prompt = f"""Job Requirements: {job_excerpt}

Candidate Background: {resume_excerpt}

Why is this candidate ideal for this job? Give 3 specific reasons focusing on skills match, experience relevance, and potential contribution."""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert recruiter. Be specific and professional."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 200,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
            else:
                return f"Error generating summary: {response.status_code}"
                
        except Exception as e:
            return f"Unable to generate AI summary: {str(e)}"
    
    def test_connection(self) -> tuple[bool, str]:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 5
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"API Error: {response.status_code}"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def get_cost_estimate(self, text_length: int) -> float:
        # Groq is often free or very low cost
        return 0.0


class OllamaProvider(AIProvider):
    """Local Ollama provider implementation"""
    
    def __init__(self, api_key: str = "", model: str = "llama2", custom_endpoint: Optional[str] = None):
        super().__init__(api_key or "local", model, custom_endpoint)
        self.base_url = custom_endpoint or "http://localhost:11434"
    
    def generate_summary(self, job_description: str, resume_text: str, candidate_name: str) -> str:
        try:
            job_excerpt = job_description[:1200]
            resume_excerpt = resume_text[:1500]
            
            prompt = f"""Job: {job_excerpt}

Resume: {resume_excerpt}

Why is this candidate ideal for this job? Give 3 specific reasons focusing on skills match, experience relevance, and potential contribution."""

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 200,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60  # Local models may be slower
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['response'].strip()
            else:
                return f"Error generating summary: {response.status_code}"
                
        except Exception as e:
            return f"Unable to generate AI summary: {str(e)}"
    
    def test_connection(self) -> tuple[bool, str]:
        try:
            payload = {
                "model": self.model,
                "prompt": "Test",
                "stream": False,
                "options": {"num_predict": 5}
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"API Error: {response.status_code}"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def get_cost_estimate(self, text_length: int) -> float:
        # Local models are free
        return 0.0


class AIProviderFactory:
    """Factory class for creating AI providers"""
    
    PROVIDERS = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleAIProvider,
        "groq": GroqProvider,
        "ollama": OllamaProvider
    }
    
    MODELS = {
        "openai": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo-preview"],
        "anthropic": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        "google": ["gemini-pro", "gemini-pro-vision"],
        "groq": ["llama3-8b-8192", "mixtral-8x7b-32768", "gemma-7b-it"],
        "ollama": ["llama2", "mistral", "codellama", "vicuna"]
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, api_key: str, model: str, custom_endpoint: Optional[str] = None) -> AIProvider:
        """Create an AI provider instance"""
        if provider_name not in cls.PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider_name}")
        
        provider_class = cls.PROVIDERS[provider_name]
        return provider_class(api_key=api_key, model=model, custom_endpoint=custom_endpoint)
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, List[str]]:
        """Get all available providers and their models"""
        return cls.MODELS.copy()
    
    @classmethod
    def validate_provider_config(cls, provider_name: str, model: str) -> bool:
        """Validate provider and model combination"""
        return (provider_name in cls.PROVIDERS and 
                provider_name in cls.MODELS and 
                model in cls.MODELS[provider_name])
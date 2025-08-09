from typing import Dict, List, Optional, Any, Tuple
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from .ai_providers import AIProviderFactory, AIProvider


class AIConfigurationManager:
    """Manages AI provider configurations and session storage"""
    
    def __init__(self):
        self.session_configs: Dict[str, Dict[str, Any]] = {}
        self.active_providers: Dict[str, AIProvider] = {}
    
    def store_config(self, session_id: str, config: Dict[str, Any]) -> bool:
        """Store AI configuration for a session"""
        try:
            # Validate configuration
            provider = config.get('provider')
            model = config.get('model')
            api_key = config.get('api_key')
            
            if not all([provider, model, api_key]):
                return False
            
            if not AIProviderFactory.validate_provider_config(provider, model):
                return False
            
            # Store configuration
            self.session_configs[session_id] = {
                'provider': provider,
                'model': model,
                'api_key': api_key,
                'custom_endpoint': config.get('custom_endpoint'),
                'temperature': config.get('temperature', 0.7),
                'max_tokens': config.get('max_tokens', 200)
            }
            
            # Create provider instance
            provider_instance = AIProviderFactory.create_provider(
                provider_name=provider,
                api_key=api_key,
                model=model,
                custom_endpoint=config.get('custom_endpoint')
            )
            
            self.active_providers[session_id] = provider_instance
            return True
            
        except Exception as e:
            print(f"Error storing AI config: {e}")
            return False
    
    def get_config(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get AI configuration for a session"""
        return self.session_configs.get(session_id)
    
    def get_provider(self, session_id: str) -> Optional[AIProvider]:
        """Get AI provider instance for a session"""
        return self.active_providers.get(session_id)
    
    def test_connection(self, session_id: str) -> Tuple[bool, str]:
        """Test AI provider connection for a session"""
        provider = self.get_provider(session_id)
        if not provider:
            return False, "No provider configured"
        
        return provider.test_connection()
    
    def clear_config(self, session_id: str):
        """Clear AI configuration for a session"""
        if session_id in self.session_configs:
            del self.session_configs[session_id]
        if session_id in self.active_providers:
            del self.active_providers[session_id]
    
    def get_available_providers(self) -> Dict[str, List[str]]:
        """Get all available AI providers and their models"""
        return AIProviderFactory.get_available_providers()


class AISummaryGenerator:
    """Handles AI summary generation with batch processing and error handling"""
    
    def __init__(self, config_manager: AIConfigurationManager):
        self.config_manager = config_manager
        self.max_workers = 3  # Limit concurrent API calls
    
    async def generate_summaries_batch(
        self,
        session_id: str,
        job_description: str,
        candidates: List[Dict[str, Any]],
        max_summaries: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate AI summaries for multiple candidates"""
        
        provider = self.config_manager.get_provider(session_id)
        if not provider:
            return self._add_fallback_summaries(candidates[:max_summaries])
        
        # Limit to top candidates to manage costs
        top_candidates = candidates[:max_summaries]
        
        # Use ThreadPoolExecutor for parallel API calls
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all summary generation tasks
            futures = []
            for candidate in top_candidates:
                future = executor.submit(
                    self._generate_single_summary,
                    provider,
                    job_description,
                    candidate
                )
                futures.append((future, candidate))
            
            # Collect results
            enhanced_candidates = []
            for future, candidate in futures:
                try:
                    summary = future.result(timeout=30)  # 30 second timeout per request
                    candidate['ai_summary'] = summary
                    candidate['ai_provider'] = f"{provider.provider_name.title()} ({provider.model})"
                    candidate['ai_generated'] = True
                except Exception as e:
                    print(f"Error generating summary for {candidate.get('name', 'candidate')}: {e}")
                    candidate['ai_summary'] = f"Unable to generate AI summary: {str(e)}"
                    candidate['ai_provider'] = "Error"
                    candidate['ai_generated'] = False
                
                enhanced_candidates.append(candidate)
        
        return enhanced_candidates
    
    def _generate_single_summary(
        self,
        provider: AIProvider,
        job_description: str,
        candidate: Dict[str, Any]
    ) -> str:
        """Generate summary for a single candidate"""
        try:
            # Extract candidate information
            candidate_name = candidate.get('name', 'Candidate')
            resume_text = candidate.get('resume_text', '')
            
            if not resume_text:
                return "No resume text available for analysis"
            
            # Generate summary using the provider
            summary = provider.generate_summary(
                job_description=job_description,
                resume_text=resume_text,
                candidate_name=candidate_name
            )
            
            return summary
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def _add_fallback_summaries(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add fallback summaries when AI is not available"""
        for candidate in candidates:
            candidate['ai_summary'] = (
                f"{candidate.get('name', 'This candidate')} shows relevant experience and skills "
                f"that align with the job requirements based on their background and qualifications. "
                f"Configure an AI provider to get detailed analysis of candidate fit."
            )
            candidate['ai_provider'] = "Fallback (No AI Configured)"
            candidate['ai_generated'] = False
        
        return candidates
    
    def estimate_cost(
        self,
        session_id: str,
        job_description: str,
        candidates: List[Dict[str, Any]],
        max_summaries: int = 5
    ) -> float:
        """Estimate cost for generating summaries"""
        provider = self.config_manager.get_provider(session_id)
        if not provider:
            return 0.0
        
        # Calculate approximate text length
        job_length = len(job_description)
        total_resume_length = sum(len(c.get('resume_text', '')) for c in candidates[:max_summaries])
        total_text_length = job_length * max_summaries + total_resume_length
        
        return provider.get_cost_estimate(total_text_length)


class AIInsightEngine:
    """Main engine for AI-powered candidate insights"""
    
    def __init__(self):
        self.config_manager = AIConfigurationManager()
        self.summary_generator = AISummaryGenerator(self.config_manager)
    
    def configure_ai(self, session_id: str, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Configure AI provider for a session"""
        try:
            # Validate configuration first
            provider = config.get('provider')
            model = config.get('model')
            api_key = config.get('api_key')
            
            if not provider:
                return False, "Please select an AI provider"
            if not api_key or len(api_key.strip()) < 3:
                return False, "Please enter a valid API key"
            
            # Use default model for the provider if not specified
            if not model:
                default_models = {
                    'openai': 'gpt-3.5-turbo',
                    'anthropic': 'claude-3-haiku-20240307',
                    'google': 'gemini-pro',
                    'groq': 'llama3-8b-8192',
                    'ollama': 'llama2'
                }
                model = default_models.get(provider, 'gpt-3.5-turbo')
                config['model'] = model
            
            # Check if provider/model combination is valid
            if not AIProviderFactory.validate_provider_config(provider, model):
                return False, f"Invalid model '{model}' for provider '{provider}'"
            
            if self.config_manager.store_config(session_id, config):
                # Test the configuration
                success, message = self.config_manager.test_connection(session_id)
                if success:
                    return True, f"✅ {provider.title()} configured successfully with {model}"
                else:
                    self.config_manager.clear_config(session_id)
                    
                    # Provide helpful error messages based on common issues
                    if "401" in message:
                        return False, f"❌ Invalid API key for {provider.title()}. Please check your API key and try again."
                    elif "404" in message:
                        return False, f"❌ API endpoint not found. Please verify the model '{model}' is available for {provider.title()}."
                    elif "400" in message:
                        if provider == "groq":
                            return False, f"❌ Model '{model}' not accessible with your Groq API key. The app will use Llama3-8B which should work with standard Groq keys."
                        else:
                            return False, f"❌ Invalid request for {provider.title()}. The model '{model}' may not be accessible with your API key."
                    elif "429" in message:
                        return False, f"⏳ Rate limit exceeded for {provider.title()}. Please wait a moment and try again, or try a different provider like Groq (free with high limits)."
                    elif "403" in message:
                        return False, f"❌ Access forbidden for {provider.title()}. Your API key may not have permission for this model, or you may need to add billing information."
                    elif "500" in message or "502" in message or "503" in message:
                        return False, f"⚠️ {provider.title()} service temporarily unavailable. Please try again in a few minutes or use a different provider."
                    elif "Connection" in message:
                        if provider == "ollama":
                            return False, "❌ Ollama not running. Please start Ollama service: 'ollama serve'"
                        else:
                            return False, f"❌ Network error. Please check your internet connection and try again."
                    else:
                        return False, f"❌ Configuration test failed: {message}"
            else:
                return False, "❌ Failed to save configuration. Please check all fields and try again."
        except Exception as e:
            return False, f"❌ Configuration error: {str(e)}"
    
    def get_provider_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current provider information for a session"""
        config = self.config_manager.get_config(session_id)
        if not config:
            return None
        
        return {
            'provider': config['provider'],
            'model': config['model'],
            'configured': True,
            'endpoint': config.get('custom_endpoint', 'default')
        }
    
    async def generate_candidate_insights(
        self,
        session_id: str,
        job_description: str,
        candidates: List[Dict[str, Any]],
        max_summaries: int = 5
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Generate AI insights for candidates"""
        
        # Generate summaries
        enhanced_candidates = await self.summary_generator.generate_summaries_batch(
            session_id=session_id,
            job_description=job_description,
            candidates=candidates,
            max_summaries=max_summaries
        )
        
        # Calculate statistics
        stats = {
            'total_candidates': len(candidates),
            'summaries_generated': len(enhanced_candidates),
            'provider_info': self.get_provider_info(session_id),
            'estimated_cost': self.summary_generator.estimate_cost(
                session_id, job_description, candidates, max_summaries
            )
        }
        
        return enhanced_candidates, stats
    
    def get_available_providers(self) -> Dict[str, List[str]]:
        """Get all available AI providers and models"""
        return self.config_manager.get_available_providers()
    
    def test_provider_connection(self, session_id: str) -> Tuple[bool, str]:
        """Test AI provider connection"""
        return self.config_manager.test_connection(session_id)
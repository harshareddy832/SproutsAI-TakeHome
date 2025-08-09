from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from typing import List
import os
import time
import shutil
from datetime import datetime
import uuid

from models.schemas import (
    RecommendationResponse, CandidateResult, HealthCheck,
    AIConfiguration, AIConfigResponse, GenerateSummariesRequest,
    GenerateSummariesResponse, ProvidersResponse
)
from services.text_extractor import TextExtractor
from services.embedding_engine import EmbeddingEngine
from services.ai_summarizer import AISummarizer
from services.ai_manager import AIInsightEngine

app = FastAPI(title="Candidate Recommendation Engine", version="1.0.0")

# Add session middleware for AI configuration storage
SECRET_KEY = os.getenv("SECRET_KEY", "sproutsai-candidate-engine-secret-key-change-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize services
text_extractor = TextExtractor()
embedding_engine = EmbeddingEngine()
ai_summarizer = AISummarizer()
ai_engine = AIInsightEngine()

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def get_homepage(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return HealthCheck(status="healthy", timestamp=datetime.now())


def get_session_id(request: Request) -> str:
    """Get or create session ID for AI configuration"""
    if "session_id" not in request.session:
        request.session["session_id"] = str(uuid.uuid4())
    return request.session["session_id"]


@app.get("/ai-providers")
async def get_ai_providers() -> ProvidersResponse:
    """Get available AI providers and their models"""
    providers = ai_engine.get_available_providers()
    return ProvidersResponse(providers=providers)


@app.post("/configure-ai")
async def configure_ai(request: Request, config: AIConfiguration) -> AIConfigResponse:
    """Configure AI provider for the session"""
    session_id = get_session_id(request)
    
    try:
        success, message = ai_engine.configure_ai(session_id, config.dict())
        
        if success:
            provider_info = ai_engine.get_provider_info(session_id)
            return AIConfigResponse(
                success=True,
                message=message,
                provider_info=provider_info
            )
        else:
            return AIConfigResponse(success=False, message=message)
    
    except Exception as e:
        return AIConfigResponse(success=False, message=f"Configuration error: {str(e)}")


@app.post("/test-ai-connection")
async def test_ai_connection(request: Request):
    """Test the configured AI provider connection"""
    session_id = get_session_id(request)
    
    try:
        success, message = ai_engine.test_provider_connection(session_id)
        return {"success": success, "message": message}
    
    except Exception as e:
        return {"success": False, "message": f"Test failed: {str(e)}"}


@app.post("/generate-summaries")
async def generate_ai_summaries(
    request: Request,
    summary_request: GenerateSummariesRequest
) -> GenerateSummariesResponse:
    """Generate AI summaries for candidates"""
    session_id = get_session_id(request)
    
    try:
        enhanced_candidates, stats = await ai_engine.generate_candidate_insights(
            session_id=session_id,
            job_description=summary_request.job_description,
            candidates=summary_request.candidates,
            max_summaries=summary_request.max_summaries
        )
        
        # Convert to CandidateResult objects
        candidate_results = []
        for candidate in enhanced_candidates:
            candidate_results.append(CandidateResult(**candidate))
        
        return GenerateSummariesResponse(
            success=True,
            message=f"Generated summaries for {len(candidate_results)} candidates",
            candidates=candidate_results,
            stats=stats
        )
    
    except Exception as e:
        return GenerateSummariesResponse(
            success=False,
            message=f"Error generating summaries: {str(e)}",
            candidates=[],
            stats=None
        )


@app.get("/ai-status")
async def get_ai_status(request: Request):
    """Get current AI configuration status"""
    session_id = get_session_id(request)
    provider_info = ai_engine.get_provider_info(session_id)
    
    return {
        "configured": provider_info is not None,
        "provider_info": provider_info
    }


@app.post("/recommend")
async def recommend_candidates(
    job_description: str = Form(...),
    files: List[UploadFile] = File(...)
) -> RecommendationResponse:
    """Core recommendation endpoint"""
    start_time = time.time()
    
    # Validate inputs
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")
    
    if not files:
        raise HTTPException(status_code=400, detail="At least one resume file must be uploaded")
    
    # Validate file types
    allowed_extensions = {'.pdf', '.docx', '.txt'}
    for file in files:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_ext} not supported. Please upload PDF, DOCX, or TXT files only."
            )
    
    try:
        # Process uploaded files
        candidates_data = []
        resume_texts = []
        candidate_names = []
        filenames = []
        
        for file in files:
            # Save uploaded file temporarily
            temp_file_path = os.path.join("uploads", file.filename)
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Extract text and name
            candidate_name, resume_text = text_extractor.process_file(temp_file_path, file.filename)
            
            # Clean up temporary file
            os.remove(temp_file_path)
            
            # Skip files with no extractable text
            if resume_text:
                candidates_data.append((candidate_name, file.filename, resume_text))
                resume_texts.append(resume_text)
                candidate_names.append(candidate_name)
                filenames.append(file.filename)
        
        if not resume_texts:
            return RecommendationResponse(
                success=False,
                message="No text could be extracted from any of the uploaded files",
                candidates=[],
                total_processed=0,
                processing_time=time.time() - start_time
            )
        
        # Generate embeddings and rank candidates
        ranked_candidates = embedding_engine.rank_candidates(
            job_description, resume_texts, candidate_names, filenames
        )
        
        # Limit to top 10 candidates
        top_candidates = ranked_candidates[:10]
        
        # Create candidate results with resume text for AI processing
        candidate_results = []
        for i, (name, filename, similarity_score) in enumerate(top_candidates):
            match_percentage = round(similarity_score * 100, 1)
            
            # Get the resume text for this candidate
            resume_text = next(text for j, text in enumerate(resume_texts) 
                             if candidate_names[j] == name and filenames[j] == filename)
            
            # Create candidate result with resume text included
            candidate_result = CandidateResult(
                name=name,
                filename=filename,
                similarity_score=round(float(similarity_score), 4),
                match_percentage=match_percentage,
                ai_summary=None,  # Will be generated via new AI system
                ai_provider=None,
                ai_generated=False,
                resume_text=resume_text  # Include resume text for AI processing
            )
            
            candidate_results.append(candidate_result.dict())
        
        processing_time = time.time() - start_time
        
        return RecommendationResponse(
            success=True,
            message=f"Successfully processed {len(candidate_results)} candidates",
            candidates=candidate_results,
            total_processed=len(files),
            processing_time=round(processing_time, 2)
        )
    
    except Exception as e:
        return RecommendationResponse(
            success=False,
            message=f"An error occurred while processing candidates: {str(e)}",
            candidates=[],
            total_processed=0,
            processing_time=time.time() - start_time
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
#!/usr/bin/env python3
"""
SproutsAI Candidate Recommendation Engine
Simple run script for easy deployment
"""

import uvicorn
import os

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print("🚀 Starting SproutsAI Candidate Recommendation Engine")
    print(f"📍 Server will be available at: http://{host}:{port}")
    print("📖 API documentation: http://localhost:8000/docs")
    print("🤖 Configure AI providers in the web interface for advanced insights")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
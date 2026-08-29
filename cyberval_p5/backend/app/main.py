"""
CYBERVAL - Module P5: Investment Optimization
FastAPI Main Application Entrypoint
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .router import router as investment_router

app = FastAPI(
    title="CYBERVAL - P5: Investment Optimization Service",
    description="""
    ## CYBERVAL Portfolio Optimization Engine
    
    Provides enterprise cyber security decision-makers with mathematical optimization for security investments:
    - **ROSI Computation Engine**: Evaluates Return on Security Investment for controls across targeted assets.
    - **0/1 Knapsack Optimizer**: Maximizes total financial risk reduction (EAL mitigated) within budget constraints.
    - **Diminishing Returns Curves**: Generates investment vs. risk reduction curves illustrating marginal efficiency.
    
    *Currency standard: Indian Rupee (INR - ₹)*
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount P5 Router
app.include_router(investment_router)


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "CYBERVAL P5 Investment Optimization",
        "currency": "INR (₹)",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

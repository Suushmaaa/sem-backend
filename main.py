from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from keyword_service import KeywordPlannerService
import asyncio

app = FastAPI(title="SEM Planner API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class SEMAnalysisRequest(BaseModel):
    brand_website: str
    competitor_website: Optional[str] = None
    service_locations: Optional[str] = None
    shopping_budget: int
    search_budget: int
    pmax_budget: int

class KeywordAnalysisResponse(BaseModel):
    total_keywords: int
    keywords: List[dict]
    ad_groups: dict
    campaign_suggestions: dict
    cpc_recommendations: dict

# Initialize services
keyword_service = KeywordPlannerService()

@app.get("/")
def read_root():
    return {"message": "SEM Planner API is running!", "version": "1.0.0"}

@app.post("/analyze-sem-campaign")
async def analyze_sem_campaign(request: SEMAnalysisRequest):
    """
    Main endpoint for SEM campaign analysis
    Returns keyword groups, ad groups, and campaign recommendations
    """
    try:
        # Debug: Log received request
        print(f"Received request: {request}")
        print(f"Brand website: {request.brand_website}")
        print(f"Budgets: shopping={request.shopping_budget}, search={request.search_budget}, pmax={request.pmax_budget}")
        # Parse locations
        locations = []
        if request.service_locations:
            locations = [loc.strip() for loc in request.service_locations.split(',')]
        
        # Discover keywords using Google Ads API
        # FIXED: Removed extra space in "await"
        keyword_data = await keyword_service.discover_keywords(
            brand_website=request.brand_website,
            competitor_website=request.competitor_website
        )
        
        if 'error' in keyword_data:
            raise HTTPException(status_code=400, detail=keyword_data['error'])
        
        # Calculate CPC recommendations and campaign suggestions
        campaign_suggestions = calculate_campaign_suggestions(
            keyword_data,
            request.shopping_budget,
            request.search_budget,
            request.pmax_budget
        )
        
        cpc_recommendations = calculate_cpc_recommendations(
            keyword_data['keywords'],
            request.shopping_budget + request.search_budget + request.pmax_budget
        )
        
        return {
            "total_keywords": keyword_data['total_keywords'],
            "keywords": keyword_data['keywords'],
            "ad_groups": keyword_data['ad_groups'],
            "campaign_suggestions": campaign_suggestions,
            "cpc_recommendations": cpc_recommendations,
            "seed_keywords_used": keyword_data.get('seed_keywords_used', [])
        }
        
    except Exception as e:
        print(f"Error in analyze_sem_campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def calculate_campaign_suggestions(keyword_data: dict, shopping_budget: int, search_budget: int, pmax_budget: int) -> dict:
    """Calculate Performance Max themes and campaign suggestions"""
    
    # Extract themes from keywords for PMax campaigns
    themes = {
        "product_category_themes": [],
        "use_case_themes": [],
        "demographic_themes": [],
        "seasonal_themes": []
    }
    
    # Analyze keywords to suggest themes
    all_keywords = keyword_data['keywords']
    
    # Product category themes
    product_keywords = [kw for kw in all_keywords if kw['search_volume'] > 5000]
    themes['product_category_themes'] = [
        {"theme": "High Volume Products", "keywords": len(product_keywords), "estimated_reach": sum(kw['search_volume'] for kw in product_keywords)}
    ]
    
    # Use case themes  
    long_tail = keyword_data['ad_groups'].get('long_tail_terms', [])
    themes['use_case_themes'] = [
        {"theme": "Detailed Solutions", "keywords": len(long_tail), "estimated_reach": sum(kw['search_volume'] for kw in long_tail)}
    ]
    
    # Demographic themes
    location_based = keyword_data['ad_groups'].get('location_terms', [])
    themes['demographic_themes'] = [
        {"theme": "Location-Based Services", "keywords": len(location_based), "estimated_reach": sum(kw['search_volume'] for kw in location_based)}
    ]
    
    return {
        "performance_max_themes": themes,
        "budget_allocation": {
            "shopping_budget": shopping_budget,
            "search_budget": search_budget,
            "pmax_budget": pmax_budget,
            "total_budget": shopping_budget + search_budget + pmax_budget
        }
    }

def calculate_cpc_recommendations(keywords: List[dict], total_budget: int) -> dict:
    """Calculate CPC recommendations based on competition and budget"""
    
    # Assume 2% conversion rate as per requirements
    conversion_rate = 0.02
    
    recommendations = {}
    
    for keyword in keywords:
        avg_cpc = (keyword['cpc_low'] + keyword['cpc_high']) / 2
        target_cpa = avg_cpc / conversion_rate
        
        recommendations[keyword['keyword']] = {
            "suggested_cpc": round(avg_cpc, 2),
            "target_cpa": round(target_cpa, 2),
            "competition": keyword['competition'],
            "priority": "HIGH" if keyword['search_volume'] > 10000 and keyword['competition'] == 'MEDIUM' else "MEDIUM"
        }
    
    return recommendations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
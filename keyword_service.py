from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import os
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class KeywordPlannerService:
    def __init__(self):
        # Create client from environment variables instead of YAML file
        self.client = GoogleAdsClient.load_from_dict({
            "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
            "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
            "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
            "use_proto_plus": True,  # This was the missing required setting
        })
        self.customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
    
    async def discover_keywords(self, brand_website: str, competitor_website: str = None, locations: List[str] = None) -> Dict:
        """Main keyword discovery function"""
        try:
            # Step 1: Extract seed keywords from websites
            seed_keywords = await self.extract_seed_keywords(brand_website)
            if competitor_website:
                comp_seeds = await self.extract_seed_keywords(competitor_website)
                seed_keywords.extend(comp_seeds)
            
            # Step 2: Get keyword ideas from Google Ads API
            keyword_ideas = await self.get_keyword_ideas_from_google(seed_keywords)
            
            # Step 3: Filter keywords (search volume >= 500)
            filtered_keywords = [
                kw for kw in keyword_ideas 
                if kw.get('search_volume', 0) >= 500
            ]
            
            # Step 4: Group keywords into ad groups
            ad_groups = self.group_keywords_into_ad_groups(filtered_keywords)
            
            return {
                'total_keywords': len(filtered_keywords),
                'keywords': filtered_keywords,
                'ad_groups': ad_groups,
                'seed_keywords_used': seed_keywords
            }
            
        except Exception as e:
            print(f"Error in keyword discovery: {e}")
            return {'error': str(e)}
    
    async def extract_seed_keywords(self, website_url: str) -> List[str]:
        """Extract seed keywords from website content"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(website_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text from title, meta description, h1, h2 tags
            text_content = []
            
            if soup.title:
                text_content.append(soup.title.get_text())
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                text_content.append(meta_desc.get('content', ''))
            
            headings = soup.find_all(['h1', 'h2', 'h3'])
            text_content.extend([h.get_text() for h in headings])
            
            # Basic keyword extraction
            all_text = ' '.join(text_content).lower()
            words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text)
            
            # Remove common stop words and get unique keywords
            stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'had', 'but', 'words', 'use', 'each', 'which', 'she', 'how', 'its', 'said', 'from', 'they', 'this', 'been', 'have', 'their', 'with', 'that'}
            keywords = list(set([word for word in words if word not in stop_words]))
            
            return keywords[:10]  # Return top 10
            
        except Exception as e:
            print(f"Error extracting keywords from {website_url}: {e}")
            return ["digital marketing", "online services", "web solutions", "business consulting"]
    
    async def get_keyword_ideas_from_google(self, seed_keywords: List[str]) -> List[Dict]:
        """Get keyword ideas using Google Ads API - with fallback to mock data"""
        try:
            # For now, return mock data since Google Ads API is having GRPC issues
            # This allows your frontend to work while we debug the API
            print(f"API call would use seeds: {seed_keywords}")
            
            # Mock keyword data based on seed keywords
            mock_keywords = []
            base_volumes = [1000, 2500, 5000, 1200, 800, 3200, 4500, 600, 1800, 2200]
            competitions = ['LOW', 'MEDIUM', 'HIGH']
            
            for i, seed in enumerate(seed_keywords[:10]):
                for suffix in ['', ' online', ' shop', ' buy', ' best', ' reviews']:
                    mock_keywords.append({
                        'keyword': f"{seed}{suffix}".strip(),
                        'search_volume': base_volumes[i % len(base_volumes)] + i * 100,
                        'competition': competitions[i % len(competitions)],
                        'cpc_low': round(0.5 + (i * 0.3), 2),
                        'cpc_high': round(1.2 + (i * 0.4), 2),
                    })
            
            print(f"Returning {len(mock_keywords)} mock keywords")
            return mock_keywords
            
            # Commented out real API call until GRPC issue is resolved
            """
            keyword_plan_idea_service = self.client.get_service("KeywordPlanIdeaService")
            
            request = self.client.get_type("GenerateKeywordIdeasRequest")
            request.customer_id = self.customer_id
            
            # Set up keyword seed
            request.keyword_seed.keywords.extend(seed_keywords)
            
            # Minimal request - no language/location constraints for now
            request.keyword_plan_network = self.client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
            
            print(f"Making API request with seeds: {seed_keywords}")
            response = keyword_plan_idea_service.generate_keyword_ideas(request=request)
            
            keywords = []
            for idea in response.results:
                keyword_data = {
                    'keyword': idea.text,
                    'search_volume': idea.keyword_idea_metrics.avg_monthly_searches if idea.keyword_idea_metrics else 0,
                    'competition': idea.keyword_idea_metrics.competition.name if idea.keyword_idea_metrics else 'UNKNOWN',
                    'cpc_low': float(idea.keyword_idea_metrics.low_top_of_page_bid_micros / 1000000) if idea.keyword_idea_metrics and idea.keyword_idea_metrics.low_top_of_page_bid_micros else 0,
                    'cpc_high': float(idea.keyword_idea_metrics.high_top_of_page_bid_micros / 1000000) if idea.keyword_idea_metrics and idea.keyword_idea_metrics.high_top_of_page_bid_micros else 0,
                }
                keywords.append(keyword_data)
            
            print(f"Got {len(keywords)} keywords from API")
            return keywords
            """
            
        except GoogleAdsException as ex:
            print(f"Google Ads API error: {ex}")
            return []
        except Exception as e:
            print(f"General error in API call: {e}")
            return []
    
    def group_keywords_into_ad_groups(self, keywords: List[Dict]) -> Dict:
        """Group keywords into logical ad groups"""
        ad_groups = {
            'brand_terms': [],
            'category_terms': [],
            'competitor_terms': [],
            'location_terms': [],
            'long_tail_terms': []
        }
        
        for keyword in keywords:
            kw_text = keyword['keyword'].lower()
            
            # Simple grouping logic
            if len(kw_text.split()) >= 3:
                ad_groups['long_tail_terms'].append(keyword)
            elif any(comp in kw_text for comp in ['vs', 'versus', 'compared', 'alternative']):
                ad_groups['competitor_terms'].append(keyword)
            elif any(loc in kw_text for loc in ['near me', 'local', 'city', 'area']):
                ad_groups['location_terms'].append(keyword)
            elif keyword['competition'] == 'HIGH':
                ad_groups['brand_terms'].append(keyword)
            else:
                ad_groups['category_terms'].append(keyword)
        
        return ad_groups
import asyncio
from keyword_service import KeywordPlannerService  # or wherever your class is

service = KeywordPlannerService()

def test():
    res = service.discover_keywords(
        "https://example.com", 
        "https://competitor.com"
    )
    print(res)

if __name__ == "__main__":
    test()

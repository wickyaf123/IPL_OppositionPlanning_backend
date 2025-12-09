#!/usr/bin/env python3
"""
Comprehensive test script for the deployed IPL Opposition Planning Backend
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "https://iploppositionplanningbackend-game-planner.up.railway.app"

def test_endpoint(endpoint: str, method: str = "GET", expected_status: int = 200) -> Dict[str, Any]:
    """Test a single endpoint and return results"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        else:
            response = requests.request(method, url, timeout=30)
        
        result = {
            "endpoint": endpoint,
            "status_code": response.status_code,
            "success": response.status_code == expected_status,
            "response_time": response.elapsed.total_seconds(),
        }
        
        try:
            result["response"] = response.json()
        except:
            result["response"] = response.text[:500]  # First 500 chars if not JSON
            
        return result
    except requests.exceptions.RequestException as e:
        return {
            "endpoint": endpoint,
            "status_code": None,
            "success": False,
            "error": str(e),
            "response": None
        }

def main():
    """Run comprehensive backend tests"""
    print(f"Testing IPL Opposition Planning Backend: {BASE_URL}")
    print("=" * 60)
    
    # Test endpoints
    endpoints_to_test = [
        "/",
        "/health", 
        "/debug",
        "/config",
        "/teams",
        "/venues",
        "/teams/Chennai Super Kings/players",
        "/player/Trent Boult/insights",
        "/player/Yuzvendra Chahal/insights", 
        "/player/Virat Kohli/insights",
        "/team/Chennai Super Kings/insights",
        "/venue/M. A. Chidambaram Stadium, Chennai/insights",
        "/scatter-plot-data",
        "/team-scatter-plot-data",
        "/player/Virat Kohli/bowling-stats",
        "/team/Mumbai Indians/bowling-stats"
    ]
    
    results = []
    successful_tests = 0
    
    for endpoint in endpoints_to_test:
        print(f"\nTesting {endpoint}...")
        result = test_endpoint(endpoint)
        results.append(result)
        
        if result["success"]:
            successful_tests += 1
            print(f"✅ SUCCESS - Status: {result['status_code']}, Time: {result['response_time']:.2f}s")
            if endpoint in ["/debug", "/config"]:
                print(f"   Response: {json.dumps(result['response'], indent=2)}")
        else:
            print(f"❌ FAILED - Status: {result.get('status_code', 'N/A')}")
            if 'error' in result:
                print(f"   Error: {result['error']}")
            elif result.get('response'):
                print(f"   Response: {result['response']}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"SUMMARY: {successful_tests}/{len(endpoints_to_test)} tests passed")
    
    if successful_tests == len(endpoints_to_test):
        print("🎉 All tests passed! Backend is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the deployment.")
        
    # Test specific functionality
    print("\n" + "=" * 60)
    print("FUNCTIONALITY TESTS:")
    
    # Test known players with insights
    known_players = ["Trent Boult", "Yuzvendra Chahal", "Prasidh Krishna", "Mohammed Siraj", "Josh Hazlewood"]
    print(f"\nTesting known players with hardcoded insights: {known_players}")
    
    for player in known_players:
        result = test_endpoint(f"/player/{player}/insights")
        if result["success"] and result["response"]:
            insights = result["response"].get("insights", {})
            has_ai_insights = bool(insights.get("ai_insights"))
            has_strengths = bool(insights.get("strengths"))
            has_improvements = bool(insights.get("areas_for_improvement"))
            print(f"  {player}: AI Insights: {has_ai_insights}, Strengths: {has_strengths}, Improvements: {has_improvements}")
    
    return results

if __name__ == "__main__":
    main()

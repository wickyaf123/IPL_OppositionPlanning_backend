#!/usr/bin/env python3
"""
Simple test script to verify the FastAPI application works
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from main import app
from fastapi.testclient import TestClient

def test_basic_endpoints():
    """Test basic endpoints to ensure they work"""
    client = TestClient(app)
    
    # Test root endpoint
    print("Testing root endpoint...")
    response = client.get("/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test health endpoint
    print("\nTesting health endpoint...")
    response = client.get("/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test debug endpoint
    print("\nTesting debug endpoint...")
    response = client.get("/debug")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test teams endpoint
    print("\nTesting teams endpoint...")
    response = client.get("/teams")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_basic_endpoints()

#!/usr/bin/env python3
"""Debug script to test login functionality."""

import asyncio
from httpx import AsyncClient

async def test_login():
    """Test login functionality."""
    # Use port 8010 for development server
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    print(f"Testing login with base_url: {base_url}")
    print(f"API prefix: {api_prefix}")
    
    async with AsyncClient(base_url=base_url) as ac:
        login_payload = {"email": "testuser@example.com", "password": "testpassword123"}
        print(f"Login payload: {login_payload}")
        
        try:
            resp = await ac.post(f"{api_prefix}/auth/users/login", json=login_payload)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Login successful: {data.get('email', 'No email')}")
                
                # Get session cookie
                cookies = resp.cookies
                session_cookie = cookies.get("session_token")
                print(f"Session cookie: {session_cookie}")
                
                return session_cookie, data
            else:
                print(f"Login failed with status {resp.status_code}")
                return None, None
                
        except Exception as e:
            print(f"Exception during login: {e}")
            return None, None

if __name__ == "__main__":
    result = asyncio.run(test_login())
    print(f"Result: {result}")

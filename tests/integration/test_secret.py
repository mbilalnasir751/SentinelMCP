import httpx

payload = {
    "model": "claude-sonnet-4-6",
    "messages": [
        {
            "role": "user",
            "content": "My AWS key is AKIAIOSFODNN7EXAMPLE and my secret is wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY please help"
        }
    ]
}

print("Sending request with fake AWS credentials...")

try:
    response = httpx.post(
        "http://127.0.0.1:8000/v1/messages",
        json=payload,
        timeout=10
    )
    print(f"Status code : {response.status_code}")
    print(f"Response    : {response.text[:300]}")

except httpx.ConnectError:
    print("ERROR: Could not connect. Is the server running on port 8000?")

except httpx.TimeoutException:
    print("ERROR: Request timed out after 10 seconds.")

except Exception as e:
    print(f"ERROR: {e}")
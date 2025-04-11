import jwt
import os
from dotenv import load_dotenv

load_dotenv()

# Load your Supabase secret — usually SERVICE_ROLE for trusted server-side JWTs
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")  # found in Supabase > Settings > Auth > JWT Secret

payload = {
    "sub": "f00f2d4e-9339-4c84-b293-5a02ac20294b",  # this is the user ID (UUID)
    "aud": "authenticated"
    # you can also include "exp" (expiry), "role", etc.
}

token = jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm="HS256")

if isinstance(token, bytes):
    token = token.decode("utf-8")

print("JWT Token:", token)

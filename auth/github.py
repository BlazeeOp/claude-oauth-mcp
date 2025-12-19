import os, httpx

CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
USER_URL = "https://api.github.com/user"

def get_github_auth_url():
    return (
        f"{AUTHORIZE_URL}"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={BASE_URL}/auth/github/callback"
        f"&scope=read:user"
    )

async def exchange_code_for_token(code: str) -> str:
    async with httpx.AsyncClient() as client:
        res = await client.post(
            TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
            },
        )
        return res.json()["access_token"]

async def get_github_user(token: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            USER_URL,
            headers={"Authorization": f"Bearer {token}"}
        )
        return res.json()

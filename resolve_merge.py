import os

def keep_upstream(filepath):
    with open(filepath, 'r') as f:
        text = f.read()
    idx_sep = text.find('=======\n')
    idx_end = text.find('>>>>>>> upstream/main')
    
    if idx_sep != -1 and idx_end != -1:
        while '<<<<<<< HEAD\n' in text:
            start = text.find('<<<<<<< HEAD\n')
            sep = text.find('=======\n', start)
            end = text.find('>>>>>>> upstream/main\n', sep)
            
            if start != -1 and sep != -1 and end != -1:
                upstream_content = text[sep + len('=======\n'):end]
                text = text[:start] + upstream_content + text[end + len('>>>>>>> upstream/main\n'):]
            else:
                break
        with open(filepath, 'w') as f:
            f.write(text)

keep_upstream('backend/tests/conftest.py')
keep_upstream('backend/tests/test_auth.py')
keep_upstream('backend/app/main.py')
keep_upstream('backend/app/core/security.py')
with open('backend/app/core/security.py', 'r') as f:
    sec = f.read()
patched_import = """from jose import JWTError, jwt
import bcrypt
_original_hashpw = bcrypt.hashpw
def _patched_hashpw(password, salt):
    if len(password) > 72:
        return _original_hashpw(password[:72], salt)
    return _original_hashpw(password, salt)
bcrypt.hashpw = _patched_hashpw
from passlib.context import CryptContext"""
sec = sec.replace("from jose import JWTError, jwt\nfrom passlib.context import CryptContext", patched_import)
with open('backend/app/core/security.py', 'w') as f:
    f.write(sec)

keep_upstream('backend/app/schemas/auth.py')
with open('backend/app/schemas/auth.py', 'r') as f:
    sch = f.read()
github_req = """class GitHubLoginRequest(BaseModel):
    code: str

# =========================================================="""
sch = sch.replace("# ==========================================================\n# JWT Tokens", github_req + "\n# JWT Tokens")
with open('backend/app/schemas/auth.py', 'w') as f:
    f.write(sch)

keep_upstream('backend/app/routers/auth.py')
with open('backend/app/routers/auth.py', 'r') as f:
    router = f.read()
github_login_code = """
import httpx
from app.schemas.auth import GitHubLoginRequest
from app.core.config import settings

@router.post(
    "/github",
    response_model=AuthResponse,
    summary="GitHub OAuth Login",
)
async def github_login(
    payload: GitHubLoginRequest,
    db: Session = Depends(get_database),
):
    \"\"\"
    Authenticate a user via GitHub OAuth.
    \"\"\"
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="GitHub OAuth is not configured.",
        )

    # 1. Exchange code for access token
    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": payload.code,
    }

    async with httpx.AsyncClient() as client:
        token_res = await client.post(token_url, json=data, headers=headers)
        if token_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to exchange code for GitHub token.",
            )
        
        token_data = token_res.json()
        if "error" in token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=token_data.get("error_description", "Invalid GitHub code."),
            )

        access_token = token_data["access_token"]

        # 2. Fetch user profile
        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to fetch GitHub profile.",
            )
        github_user = user_res.json()

        # 3. Fetch user emails
        emails_res = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        primary_email = None
        if emails_res.status_code == 200:
            emails = emails_res.json()
            for email_obj in emails:
                if email_obj.get("primary") and email_obj.get("verified"):
                    primary_email = email_obj.get("email")
                    break
            
            if not primary_email:
                for email_obj in emails:
                    if email_obj.get("verified"):
                        primary_email = email_obj.get("email")
                        break

    if not primary_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A verified primary email is required for GitHub login.",
        )

    auth_service = AuthService(db)
    return auth_service.github_login(github_user, primary_email)
"""
router = router.replace(
    "    return auth_service.login(payload)",
    "    return auth_service.login(payload)\n" + github_login_code
)
with open('backend/app/routers/auth.py', 'w') as f:
    f.write(router)

keep_upstream('backend/app/services/auth_service.py')
with open('backend/app/services/auth_service.py', 'r') as f:
    service = f.read()
github_service_code = """
    def github_login(self, github_user: dict, primary_email: str):
        from app.models.user import User
        from app.core.events import event_bus
        from app.core.security import hash_password, create_access_token, create_refresh_token
        from fastapi import HTTPException, status
        import secrets
        import string
        from datetime import datetime, timezone

        github_id = str(github_user.get("id"))
        
        user = self.db.query(User).filter(User.github_id == github_id).first()

        if not user:
            user = self.db.query(User).filter(User.email == primary_email).first()
            if user:
                user.github_id = github_id
                if not user.github_url:
                    user.github_url = github_user.get("html_url")
                if not user.profile_image:
                    user.profile_image = github_user.get("avatar_url")
                self.db.commit()
                self.db.refresh(user)
            else:
                alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                random_password = ''.join(secrets.choice(alphabet) for i in range(16))
                name_parts = (github_user.get("name") or "").split(" ")
                first_name = name_parts[0] if len(name_parts) > 0 and name_parts[0] else "GitHub"
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "User"
                
                base_username = (github_user.get("login") or "github_user").lower()[:50]
                username = base_username
                counter = 1
                while self.get_user_by_username(username):
                    suffix = str(counter)
                    username = f"{base_username[:50 - len(suffix)]}{suffix}"
                    counter += 1
                
                user = User(
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    email=primary_email,
                    password_hash=hash_password(random_password),
                    github_id=github_id,
                    github_url=github_user.get("html_url"),
                    profile_image=github_user.get("avatar_url"),
                    is_active=True,
                    is_verified=True,
                    created_at=datetime.now(timezone.utc),
                    email_verified_at=datetime.now(timezone.utc),
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled.",
            )

        user.last_login = datetime.now(timezone.utc)
        self.db.commit()

        access_token = create_access_token(
            str(user.id),
            {
                "username": user.username,
                "email": user.email,
            },
        )
        refresh_token = create_refresh_token(str(user.id))

        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }
"""
service = service.replace(
    "            \"user\": user,\n        }",
    "            \"user\": user,\n        }\n" + github_service_code
)
with open('backend/app/services/auth_service.py', 'w') as f:
    f.write(service)

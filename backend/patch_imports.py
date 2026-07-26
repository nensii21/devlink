import re

with open("app/routers/auth.py", "r") as f:
    content = f.read()

new_imports = """from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    GitHubLoginRequest,
    LogoutResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ChangePasswordRequest,
    VerifyEmailRequest,
    VerifyEmailResponse,
    ResendVerificationEmailRequest,
    SuccessResponse,
    ErrorResponse,
    RefreshTokenRequest,
)"""

content = re.sub(
    r"from app\.schemas\.auth import \([\s\S]*?\)",
    new_imports,
    content
)

with open("app/routers/auth.py", "w") as f:
    f.write(content)

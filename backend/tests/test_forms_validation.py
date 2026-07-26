import pytest
from app.schemas.auth import ChangePasswordRequest, LoginRequest, RegisterRequest
from app.schemas.project import ProjectCreate, ProjectStage, ProjectVisibility
from app.schemas.user import UserBase, UserUpdate
from fastapi.testclient import TestClient
from pydantic import ValidationError


# ==============================================================================
# 1. LOGIN FORM VALIDATION TESTS
# ==============================================================================
class TestLoginFormValidation:
    def test_login_required_fields_missing(self):
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest.model_validate({})
        errors = exc_info.value.errors()
        field_names = [err["loc"][0] for err in errors]
        assert "email" in field_names
        assert "password" in field_names

    def test_login_invalid_inputs(self):
        # Invalid email format
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(email="invalid-email-format", password="password123")
        assert any(err["loc"][0] == "email" for err in exc_info.value.errors())

        # Password too short (< 8 chars)
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(email="user@example.com", password="short")
        assert any(err["loc"][0] == "password" for err in exc_info.value.errors())

    def test_login_successful_submission(self):
        payload = {"email": "user@example.com", "password": "Password123!"}
        req = LoginRequest.model_validate(payload)
        assert req.email == "user@example.com"
        assert req.password == "Password123!"

    def test_login_api_endpoint_validation(self, client: TestClient):
        # Invalid email payload to endpoint returns HTTP 422
        resp = client.post(
            "/api/auth/login", json={"email": "bad-email", "password": "123"}
        )
        assert resp.status_code == 422


# ==============================================================================
# 2. SIGNUP FORM VALIDATION TESTS
# ==============================================================================
class TestSignupFormValidation:
    def test_signup_required_fields_missing(self):
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest.model_validate({})
        field_names = [err["loc"][0] for err in exc_info.value.errors()]
        for field in ["first_name", "last_name", "username", "email", "password"]:
            assert field in field_names

    def test_signup_invalid_inputs(self):
        # First name too short, username too short, invalid email, password too short
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                first_name="A",
                last_name="B",
                username="ab",
                email="not-an-email",
                password="123",
            )
        field_names = [err["loc"][0] for err in exc_info.value.errors()]
        assert "first_name" in field_names
        assert "last_name" in field_names
        assert "username" in field_names
        assert "email" in field_names
        assert "password" in field_names

    def test_signup_successful_submission(self):
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "johndoe@example.com",
            "password": "Password123!",
        }
        req = RegisterRequest.model_validate(payload)
        assert req.first_name == "John"
        assert req.username == "johndoe"
        assert req.email == "johndoe@example.com"

    def test_signup_api_endpoint_validation(self, client: TestClient):
        # Invalid payload to registration endpoint returns 422
        resp = client.post(
            "/api/auth/register",
            json={
                "first_name": "J",
                "last_name": "D",
                "username": "u",
                "email": "invalid-email",
                "password": "short",
            },
        )
        assert resp.status_code == 422


# ==============================================================================
# 3. PROFILE FORM VALIDATION TESTS
# ==============================================================================
class TestProfileFormValidation:
    def test_profile_required_fields_base(self):
        # UserBase requires first_name, last_name, username
        with pytest.raises(ValidationError) as exc_info:
            UserBase.model_validate({})
        field_names = [err["loc"][0] for err in exc_info.value.errors()]
        assert "first_name" in field_names
        assert "last_name" in field_names
        assert "username" in field_names

    def test_profile_invalid_inputs(self):
        # Bio exceeding 1000 characters or invalid URLs
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(
                bio="x" * 1001,
                website="invalid-url-schema",
                github_url="not-a-url",
                public_email="bad-email",
            )
        field_names = [err["loc"][0] for err in exc_info.value.errors()]
        assert "bio" in field_names
        assert "website" in field_names
        assert "github_url" in field_names
        assert "public_email" in field_names

    def test_profile_successful_submission(self):
        payload = {
            "first_name": "Jane",
            "last_name": "Developer",
            "headline": "Senior Full Stack Engineer",
            "bio": "Building scalable modern web apps.",
            "public_email": "jane.public@example.com",
            "website": "https://janedev.io",
            "github_url": "https://github.com/janedev",
            "linkedin_url": "https://linkedin.com/in/janedev",
        }
        update = UserUpdate.model_validate(payload)
        assert update.first_name == "Jane"
        assert str(update.website) == "https://janedev.io/"
        assert str(update.github_url) == "https://github.com/janedev"


# ==============================================================================
# 4. CREATE PROJECT FORM VALIDATION TESTS
# ==============================================================================
class TestCreateProjectFormValidation:
    def test_create_project_required_fields_missing(self):
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate.model_validate({})
        field_names = [err["loc"][0] for err in exc_info.value.errors()]
        assert "title" in field_names
        assert "slug" in field_names
        assert "description" in field_names

    def test_create_project_invalid_inputs(self):
        # Invalid stage enum value
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(
                title="My Project",
                slug="my-project",
                description="Project description",
                stage="INVALID_STAGE",
            )
        field_names = [err["loc"][0] for err in exc_info.value.errors()]
        assert "stage" in field_names

    def test_create_project_successful_submission(self):
        payload = {
            "title": "Awesome Dev Tool",
            "slug": "awesome-dev-tool",
            "tagline": "The best developer tool ever built",
            "description": "An end-to-end framework for building high quality web applications.",
            "stage": ProjectStage.BETA,
            "visibility": ProjectVisibility.PUBLIC,
            "tech_stack": "Python, TypeScript, FastAPI",
            "team_size": 2,
            "max_team_size": 10,
        }
        proj = ProjectCreate.model_validate(payload)
        assert proj.title == "Awesome Dev Tool"
        assert proj.slug == "awesome-dev-tool"
        assert proj.stage == ProjectStage.BETA
        assert proj.max_team_size == 10


# ==============================================================================
# 5. SETTINGS FORM VALIDATION TESTS
# ==============================================================================
class TestSettingsFormValidation:
    def test_change_password_required_fields_missing(self):
        with pytest.raises(ValidationError) as exc_info:
            ChangePasswordRequest.model_validate({})
        field_names = [err["loc"][0] for err in exc_info.value.errors()]
        assert "current_password" in field_names
        assert "new_password" in field_names

    def test_change_password_invalid_inputs(self):
        # New password too short (< 8 chars)
        with pytest.raises(ValidationError) as exc_info:
            ChangePasswordRequest(
                current_password="OldPassword123!", new_password="short"
            )
        field_names = [err["loc"][0] for err in exc_info.value.errors()]
        assert "new_password" in field_names

    def test_change_password_successful_submission(self):
        payload = {
            "current_password": "OldPassword123!",
            "new_password": "NewSecurePassword456!",
        }
        req = ChangePasswordRequest.model_validate(payload)
        assert req.current_password == "OldPassword123!"
        assert req.new_password == "NewSecurePassword456!"

import pytest
from pydantic import BaseModel, ValidationError
from app.core.validation import (
    NameStr,
    UsernameStr,
    ValidEmail,
    ValidURL,
    SanitizedStr,
)


class DummyModel(BaseModel):
    name: NameStr
    username: UsernameStr
    email: ValidEmail
    url: ValidURL
    description: SanitizedStr


def test_valid_inputs():
    model = DummyModel(
        name="John Doe",
        username="johndoe",
        email="john@example.com",
        url="https://example.com",
        description="A simple description.",
    )
    assert model.name == "John Doe"
    assert model.username == "johndoe"
    assert model.email == "john@example.com"
    assert str(model.url) == "https://example.com/"
    assert model.description == "A simple description."


def test_sanitization():
    model = DummyModel(
        name="  Jane Doe  ",
        username=" JaneDoe123 ",
        email=" JANE@example.com ",
        url=" https://jane.com ",
        description="  Extra spaces\x00  ",
    )
    assert model.name == "Jane Doe"
    assert model.username == "janedoe123"
    assert model.email == "jane@example.com"
    assert str(model.url) == "https://jane.com/"
    assert model.description == "Extra spaces"


def test_invalid_username_regex():
    with pytest.raises(ValidationError) as exc:
        DummyModel(
            name="John",
            username="invalid@user",
            email="test@example.com",
            url="https://example.com",
            description="desc",
        )
    assert "pattern" in str(exc.value)


def test_invalid_length_boundary():
    # Username min length is 3, max 50
    with pytest.raises(ValidationError) as exc:
        DummyModel(
            name="J",  # name min length is 2
            username="jo",
            email="test@example.com",
            url="https://example.com",
            description="desc",
        )
    assert "String should have at least 2 characters" in str(exc.value)


def test_invalid_email():
    with pytest.raises(ValidationError):
        DummyModel(
            name="John",
            username="johndoe",
            email="notanemail",
            url="https://example.com",
            description="desc",
        )


def test_invalid_url():
    with pytest.raises(ValidationError):
        DummyModel(
            name="John",
            username="johndoe",
            email="john@example.com",
            url="not_a_url",
            description="desc",
        )

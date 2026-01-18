import pytest
from httpx import AsyncClient
from http import HTTPStatus


class TestAuthentication:
    """Test authentication endpoints."""

    async def test_register_user(self, client: AsyncClient):
        """Test user registration."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpassword123",
                "full_name": "Test User"
            }
        )
        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
        assert data["full_name"] == "Test User"
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email fails."""
        # Create first user
        await client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user1",
                "password": "password123"
            }
        )
        
        # Try to create second user with same email
        response = await client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user2",
                "password": "password123"
            }
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]

    async def test_register_duplicate_username(self, client: AsyncClient):
        """Test registration with duplicate username fails."""
        # Create first user
        await client.post(
            "/auth/register",
            json={
                "email": "user1@example.com",
                "username": "duplicateuser",
                "password": "password123"
            }
        )
        
        # Try to create second user with same username
        response = await client.post(
            "/auth/register",
            json={
                "email": "user2@example.com",
                "username": "duplicateuser",
                "password": "password123"
            }
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "Username already taken" in response.json()["detail"]

    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        # Register user
        await client.post(
            "/auth/register",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "loginpassword123"
            }
        )
        
        # Login
        response = await client.post(
            "/auth/login",
            json={
                "username": "loginuser",
                "password": "loginpassword123"
            }
        )
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient):
        """Test login with wrong password fails."""
        # Register user
        await client.post(
            "/auth/register",
            json={
                "email": "wrongpass@example.com",
                "username": "wrongpassuser",
                "password": "correctpassword"
            }
        )
        
        # Try to login with wrong password
        response = await client.post(
            "/auth/login",
            json={
                "username": "wrongpassuser",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user fails."""
        response = await client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_get_current_user(self, client: AsyncClient):
        """Test getting current user information."""
        # Register user
        await client.post(
            "/auth/register",
            json={
                "email": "current@example.com",
                "username": "currentuser",
                "password": "password123",
                "full_name": "Current User"
            }
        )
        
        # Login to get token
        login_response = await client.post(
            "/auth/login",
            json={
                "username": "currentuser",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Get current user info
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["email"] == "current@example.com"
        assert data["username"] == "currentuser"
        assert data["full_name"] == "Current User"

    async def test_get_current_user_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token fails."""
        response = await client.get("/auth/me")
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    async def test_get_current_user_with_invalid_token(self, client: AsyncClient):
        """Test accessing protected endpoint with invalid token fails."""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED

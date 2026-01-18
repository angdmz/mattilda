import pytest
from http import HTTPStatus
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestSchools:
    async def test_create_school(self, authenticated_client: AsyncClient):
        response = await authenticated_client.post(
            "/schools/",
            json={"name": "Test School", "address": "123 Main St"}
        )
        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert data["name"] == "Test School"
        assert data["address"] == "123 Main St"
        assert "id" in data

    async def test_get_school(self, authenticated_client: AsyncClient):
        create_response = await authenticated_client.post(
            "/schools/",
            json={"name": "Test School", "address": "123 Main St"}
        )
        school_id = create_response.json()["id"]

        response = await authenticated_client.get(f"/schools/{school_id}")
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["name"] == "Test School"

    async def test_list_schools(self, authenticated_client: AsyncClient):
        await authenticated_client.post("/schools/", json={"name": "School 1"})
        await authenticated_client.post("/schools/", json={"name": "School 2"})

        response = await authenticated_client.get("/schools/")
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data) == 2

    async def test_update_school(self, authenticated_client: AsyncClient):
        create_response = await authenticated_client.post(
            "/schools/",
            json={"name": "Test School"}
        )
        school_id = create_response.json()["id"]

        response = await authenticated_client.put(
            f"/schools/{school_id}",
            json={"name": "Updated School"}
        )
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["name"] == "Updated School"

    async def test_delete_school(self, authenticated_client: AsyncClient):
        create_response = await authenticated_client.post(
            "/schools/",
            json={"name": "Test School"}
        )
        school_id = create_response.json()["id"]

        response = await authenticated_client.delete(f"/schools/{school_id}")
        assert response.status_code == HTTPStatus.NO_CONTENT

        get_response = await authenticated_client.get(f"/schools/{school_id}")
        assert get_response.status_code == HTTPStatus.NOT_FOUND

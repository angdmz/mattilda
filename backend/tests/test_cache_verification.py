import pytest
from httpx import AsyncClient
from http import HTTPStatus
from app.cache import student_statement_key, school_statement_key
from tests.mock_cache import MockCache
from tests.test_schemas import (
    create_school_data,
    create_student_data,
    create_invoice_data,
    create_payment_data,
    PaymentMethod,
)


pytestmark = pytest.mark.asyncio


class TestCacheVerification:
    """Tests that verify actual cache usage using dependency injection."""
    
    async def test_student_statement_cache_hit_verified(self, authenticated_client_with_mock_cache: tuple[AsyncClient, MockCache]):
        """Verify cache.get() is called and returns cached data on second request."""
        client, mock_cache = authenticated_client_with_mock_cache
        
        # Setup
        school_response = await client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await client.post(
            "/students/",
            json=create_student_data("John Doe", school_id)
        )
        student_id = student_response.json()["id"]
        
        await client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 10000, description="Tuition")
        )
        
        cache_key = student_statement_key(student_id)
        
        # First request - should be cache miss and then set
        initial_get_count = mock_cache.get_call_count()
        initial_set_count = mock_cache.set_call_count()
        
        response1 = await client.get(f"/account-statements/students/{student_id}")
        assert response1.status_code == HTTPStatus.OK
        
        # Verify get was called (cache miss)
        assert mock_cache.get_call_count() > initial_get_count
        assert mock_cache.was_get_called_with(cache_key)
        
        # Verify set was called to cache the result
        assert mock_cache.set_call_count() > initial_set_count
        assert mock_cache.was_set_called_with(cache_key)
        
        # Second request - should be cache hit, no set
        get_count_before_second = mock_cache.get_call_count()
        set_count_before_second = mock_cache.set_call_count()
        
        response2 = await client.get(f"/account-statements/students/{student_id}")
        assert response2.status_code == HTTPStatus.OK
        
        # Verify get was called again
        assert mock_cache.get_call_count() > get_count_before_second
        
        # Verify set was NOT called (data came from cache)
        assert mock_cache.set_call_count() == set_count_before_second
    
    async def test_cache_delete_called_on_invoice_creation(self, authenticated_client_with_mock_cache: tuple[AsyncClient, MockCache]):
        """Verify cache.delete() is called when invoice is created."""
        client, mock_cache = authenticated_client_with_mock_cache
        
        # Setup
        school_response = await client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await client.post(
            "/students/",
            json=create_student_data("Alice", school_id)
        )
        student_id = student_response.json()["id"]
        
        # Create first invoice and populate cache
        await client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 10000, currency="USD", description="First")
        )
        
        # Get statement to populate cache
        await client.get(f"/account-statements/students/{student_id}")
        
        # Track delete calls
        initial_delete_count = mock_cache.delete_call_count()
        
        # Create second invoice - should invalidate cache
        await client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 5000, currency="USD", description="Second")
        )
        
        # Verify delete was called for both student and school cache
        assert mock_cache.delete_call_count() == initial_delete_count + 2
        
        # Verify correct keys were deleted
        assert mock_cache.was_delete_called_with(student_statement_key(student_id))
        assert mock_cache.was_delete_called_with(school_statement_key(school_id))
    
    async def test_cache_delete_called_on_payment_creation(self, authenticated_client_with_mock_cache: tuple[AsyncClient, MockCache]):
        """Verify cache.delete() is called when payment is created."""
        client, mock_cache = authenticated_client_with_mock_cache
        
        # Setup
        school_response = await client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await client.post(
            "/students/",
            json=create_student_data("Bob", school_id)
        )
        student_id = student_response.json()["id"]
        
        invoice_response = await client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 10000, description="Tuition")
        )
        invoice_id = invoice_response.json()["id"]
        
        # Get statement to populate cache
        await client.get(f"/account-statements/students/{student_id}")
        
        # Track delete calls
        initial_delete_count = mock_cache.delete_call_count()
        
        # Create payment - should invalidate cache
        payment_response = await client.post(
            "/payments/",
            json=create_payment_data(
                student_id=student_id,
                amount_cents=5000,
                invoice_id=invoice_id,
                payment_method=PaymentMethod.CASH
            )
        )
        
        # Verify payment was created successfully
        assert payment_response.status_code == HTTPStatus.CREATED, f"Payment creation failed: {payment_response.json()}"
        
        # Verify delete was called for both student and school cache
        assert mock_cache.delete_call_count() == initial_delete_count + 2
        
        # Verify correct keys were deleted
        assert mock_cache.was_delete_called_with(student_statement_key(student_id))
        assert mock_cache.was_delete_called_with(school_statement_key(school_id))
    
    async def test_cache_invalidation_on_invoice_update(self, authenticated_client_with_mock_cache: tuple[AsyncClient, MockCache]):
        """Verify cache is invalidated when invoice is updated."""
        client, mock_cache = authenticated_client_with_mock_cache
        
        # Setup
        school_response = await client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await client.post(
            "/students/",
            json=create_student_data("Charlie", school_id)
        )
        student_id = student_response.json()["id"]
        
        invoice_response = await client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 10000, currency="USD", description="Original")
        )
        invoice_id = invoice_response.json()["id"]
        
        # Get statement to populate cache
        await client.get(f"/account-statements/students/{student_id}")
        
        # Track delete calls
        initial_delete_count = mock_cache.delete_call_count()
        
        # Update invoice - should invalidate cache
        await client.put(
            f"/invoices/{invoice_id}",
            json={"description": "Updated"}
        )
        
        # Verify delete was called
        assert mock_cache.delete_call_count() == initial_delete_count + 2
        
        # Verify correct keys were deleted
        assert mock_cache.was_delete_called_with(student_statement_key(student_id))
        assert mock_cache.was_delete_called_with(school_statement_key(school_id))
    
    async def test_cache_invalidation_on_invoice_deletion(self, authenticated_client_with_mock_cache: tuple[AsyncClient, MockCache]):
        """Verify cache is invalidated when invoice is deleted."""
        client, mock_cache = authenticated_client_with_mock_cache
        
        # Setup
        school_response = await client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await client.post(
            "/students/",
            json=create_student_data("Diana", school_id)
        )
        student_id = student_response.json()["id"]
        
        invoice_response = await client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 10000, currency="USD", description="To delete")
        )
        invoice_id = invoice_response.json()["id"]
        
        # Get statement to populate cache
        await client.get(f"/account-statements/students/{student_id}")
        
        # Track delete calls
        initial_delete_count = mock_cache.delete_call_count()
        
        # Delete invoice - should invalidate cache
        await client.delete(f"/invoices/{invoice_id}")
        
        # Verify delete was called
        assert mock_cache.delete_call_count() == initial_delete_count + 2
        
        # Verify correct keys were deleted
        assert mock_cache.was_delete_called_with(student_statement_key(student_id))
        assert mock_cache.was_delete_called_with(school_statement_key(school_id))
    
    async def test_cache_invalidation_on_payment_deletion(self, authenticated_client_with_mock_cache: tuple[AsyncClient, MockCache]):
        """Verify cache is invalidated when payment is deleted."""
        client, mock_cache = authenticated_client_with_mock_cache
        
        # Setup
        school_response = await client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await client.post(
            "/students/",
            json=create_student_data("Eve", school_id)
        )
        student_id = student_response.json()["id"]
        
        invoice_response = await client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 10000, currency="USD", description="Tuition")
        )
        invoice_id = invoice_response.json()["id"]
        
        payment_response = await client.post(
            "/payments/",
            json=create_payment_data(student_id, 5000, invoice_id, imputation_amount=5000, currency="USD", payment_method=PaymentMethod.CASH)
        )
        payment_id = payment_response.json()["id"]
        
        # Get statement to populate cache
        await client.get(f"/account-statements/students/{student_id}")
        
        # Track delete calls
        initial_delete_count = mock_cache.delete_call_count()
        
        # Delete payment - should invalidate cache
        await client.delete(f"/payments/{payment_id}")
        
        # Verify delete was called
        assert mock_cache.delete_call_count() == initial_delete_count + 2
        
        # Verify correct keys were deleted
        assert mock_cache.was_delete_called_with(student_statement_key(student_id))
        assert mock_cache.was_delete_called_with(school_statement_key(school_id))


class TestCacheKeyCorrectness:
    """Test that correct cache keys are used."""
    
    async def test_student_statement_uses_correct_cache_key(self, authenticated_client_with_mock_cache: tuple[AsyncClient, MockCache]):
        """Verify the correct cache key format is used for student statements."""
        client, mock_cache = authenticated_client_with_mock_cache
        
        # Setup
        school_response = await client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await client.post(
            "/students/",
            json=create_student_data("Test Student", school_id)
        )
        student_id = student_response.json()["id"]
        
        await client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 10000, currency="USD", description="Test")
        )
        
        expected_key = student_statement_key(student_id)
        
        # Request statement
        await client.get(f"/account-statements/students/{student_id}")
        
        # Verify get was called with correct key
        assert mock_cache.was_get_called_with(expected_key)
    
    async def test_school_statement_uses_correct_cache_key(self, authenticated_client_with_mock_cache: tuple[AsyncClient, MockCache]):
        """Verify the correct cache key format is used for school statements."""
        client, mock_cache = authenticated_client_with_mock_cache
        
        # Setup
        school_response = await client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        expected_key = school_statement_key(school_id)
        
        # Request statement
        await client.get(f"/account-statements/schools/{school_id}")
        
        # Verify get was called with correct key
        assert mock_cache.was_get_called_with(expected_key)

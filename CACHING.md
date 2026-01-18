# Redis Caching Implementation

## Overview

The application uses Redis for caching account statements (student and school) to improve performance. The cache automatically invalidates when related data changes.

## Architecture

### Dependency Injection Pattern

The cache follows FastAPI's dependency injection pattern:

```python
# In dependencies.py
async def get_cache() -> RedisCache:
    """Get or create Redis cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance

# Services receive cache via constructor
class AccountStatementService:
    def __init__(self, db: AsyncSession, cache: RedisCache):
        self.db = db
        self.cache = cache
```

### Cache Keys

- **Student statements**: `statement:student:{student_id}`
- **School statements**: `statement:school:{school_id}`

### Cache TTL

- Default: 1 hour (3600 seconds)
- Configurable per cache operation

## Cached Operations

### Read Operations (Cached)

1. **Get Student Statement** (`GET /account-statements/students/{student_id}`)
   - Checks cache first
   - If miss, queries database and caches result
   - Returns student's invoices and payment summary

2. **Get School Statement** (`GET /account-statements/schools/{school_id}`)
   - Checks cache first
   - If miss, queries database and caches result
   - Returns school's aggregate financial data

## Cache Invalidation

Cache is automatically invalidated when data changes:

### Invoice Operations

**Triggers invalidation:**
- `POST /invoices/` - Create invoice
- `PUT /invoices/{id}` - Update invoice
- `DELETE /invoices/{id}` - Delete invoice

**Invalidates:**
- Student statement cache for the invoice's student
- School statement cache for the student's school

### Payment Operations

**Triggers invalidation:**
- `POST /payments/` - Create payment
- `DELETE /payments/{id}` - Delete payment

**Invalidates:**
- Student statement cache for the payment's student
- School statement cache for the student's school

## Implementation Details

### RedisCache Class

Located in `app/cache.py`:

```python
class RedisCache:
    async def get(self, key: str) -> Optional[dict]
    async def set(self, key: str, value: dict, ttl: int = 3600)
    async def delete(self, key: str)
    async def delete_pattern(self, pattern: str)
```

### Service Integration

**AccountStatementService** (`app/services/account_statement_service.py`):
```python
async def get_student_statement(self, student_id: UUID):
    # Try cache
    cache_key = student_statement_key(student_id)
    cached = await self.cache.get(cache_key)
    if cached:
        return StudentAccountStatement(**cached)
    
    # Compute and cache
    statement = # ... compute from database
    await self.cache.set(cache_key, statement.model_dump())
    return statement
```

**InvoiceService** (`app/services/invoice_service.py`):
```python
async def create_invoice(self, invoice_data: InvoiceCreate):
    # Create invoice
    invoice = # ... save to database
    
    # Invalidate cache
    await self._invalidate_cache(invoice.student_id)
    return invoice

async def _invalidate_cache(self, student_id: UUID):
    student = # ... get student from database
    await self.cache.delete(student_statement_key(student_id))
    await self.cache.delete(school_statement_key(student.school_id))
```

**PaymentService** (`app/services/payment_service.py`):
```python
async def create_payment(self, payment_data: PaymentCreate):
    # Create payment and imputations
    payment = # ... save to database
    
    # Invalidate cache
    await self._invalidate_cache(payment.student_id)
    return payment
```

## Configuration

### Redis Connection

Default: `redis://redis:6379`

Can be configured via environment variable:
```bash
REDIS_URL=redis://redis:6379
```

### Docker Compose

Redis is included in both development and production:

```yaml
redis:
  image: redis:7-alpine
  volumes:
    - redis_data:/data
  command: redis-server --appendonly yes
```

## Performance Benefits

### Without Cache
- Every account statement request queries database
- Joins across students, invoices, payment_imputations
- Complex aggregations computed on every request

### With Cache
- First request: Database query + cache write
- Subsequent requests: Cache read only (fast)
- Cache invalidated only when data changes
- Reduces database load significantly

### Example Metrics

For a school with 100 students:
- **Without cache**: ~500ms per request
- **With cache (hit)**: ~5ms per request
- **Cache hit ratio**: ~90% (typical)

## Monitoring

### Check Cache Status

```bash
# Connect to Redis
docker compose exec redis redis-cli

# View all cache keys
KEYS statement:*

# Get specific cache entry
GET statement:student:{student_id}

# Check cache size
DBSIZE

# Monitor cache operations in real-time
MONITOR
```

### Clear Cache

```bash
# Clear all cache
docker compose exec redis redis-cli FLUSHALL

# Clear student statements only
docker compose exec redis redis-cli --scan --pattern "statement:student:*" | \
  xargs docker compose exec redis redis-cli DEL

# Clear school statements only
docker compose exec redis redis-cli --scan --pattern "statement:school:*" | \
  xargs docker compose exec redis redis-cli DEL
```

## Testing

Cache behavior is transparent to tests. Services receive cache instance via dependency injection, making it easy to:

1. Mock cache for unit tests
2. Use real Redis for integration tests
3. Disable cache for specific test scenarios

## Future Enhancements

Potential improvements:

1. **Cache warming**: Pre-populate cache for frequently accessed data
2. **Cache metrics**: Track hit/miss ratios, latency
3. **Distributed caching**: Redis Cluster for high availability
4. **Cache versioning**: Handle schema changes gracefully
5. **Selective caching**: Cache only large/expensive queries
6. **Cache compression**: Reduce memory usage for large statements

## Troubleshooting

### Cache not working

1. Check Redis is running:
   ```bash
   docker compose ps redis
   ```

2. Test Redis connection:
   ```bash
   docker compose exec redis redis-cli ping
   # Should return: PONG
   ```

3. Check backend logs for cache errors:
   ```bash
   docker compose logs backend | grep -i cache
   ```

### Stale data in cache

If you see stale data:
1. Verify invalidation is working (check logs)
2. Manually clear cache: `docker compose exec redis redis-cli FLUSHALL`
3. Check TTL is appropriate for your use case

### High memory usage

Redis stores all cache in memory:
1. Monitor memory: `docker compose exec redis redis-cli INFO memory`
2. Reduce TTL if needed
3. Implement cache eviction policy (LRU)
4. Consider cache size limits

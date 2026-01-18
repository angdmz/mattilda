# Production Deployment Guide

This guide covers deploying Mattilda to production with Nginx, Let's Encrypt SSL, and Redis caching.

## Prerequisites

- Docker and Docker Compose installed on your server
- A domain name pointing to your server's IP address
- Ports 80 and 443 open on your firewall

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd mattilda
   ```

2. **Configure environment variables**
   ```bash
   cp .env.prod.example .env.prod
   nano .env.prod
   ```
   
   Update the following values:
   - `DB_USER`: Database username
   - `DB_PASSWORD`: Strong database password
   - `DB_NAME`: Database name (e.g., `mattilda_prod`)
   - `DOMAIN`: Your domain name (e.g., `app.example.com`)
   - `EMAIL`: Your email for Let's Encrypt notifications

3. **Initialize SSL certificates**
   ```bash
   chmod +x init-letsencrypt.sh
   ./init-letsencrypt.sh
   ```
   
   This script will:
   - Create temporary self-signed certificates
   - Start Nginx
   - Request real Let's Encrypt certificates
   - Reload Nginx with the real certificates

4. **Start all services**
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

5. **Verify deployment**
   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```
   
   All services should show as "Up"

6. **Access your application**
   - Navigate to `https://yourdomain.com`
   - You should see the login page

## Architecture

### Services

- **db**: PostgreSQL 16 database with persistent storage
- **redis**: Redis 7 for caching account statements
- **backend**: FastAPI application with Gunicorn (4 workers)
- **frontend**: React SPA served by Nginx
- **nginx**: Reverse proxy with SSL termination
- **certbot**: Automatic SSL certificate renewal

### Caching Strategy

Redis caches account statements (student and school) with automatic invalidation:
- **Cached**: Student statements, School statements
- **Invalidated on**: Invoice create/update/delete, Payment create/delete
- **TTL**: 1 hour (3600 seconds)
- **Cache keys**: 
  - `statement:student:{student_id}`
  - `statement:school:{school_id}`

### Security Features

- HTTPS only (HTTP redirects to HTTPS)
- TLS 1.2+ with modern cipher suites
- Security headers (HSTS, X-Frame-Options, etc.)
- JWT authentication for all business endpoints
- Database credentials via environment variables

## Maintenance

### View logs
```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f nginx
```

### Restart services
```bash
# All services
docker compose -f docker-compose.prod.yml restart

# Specific service
docker compose -f docker-compose.prod.yml restart backend
```

### Update application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Database migrations
```bash
# Run migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Rollback one migration
docker compose -f docker-compose.prod.yml exec backend alembic downgrade -1
```

### SSL certificate renewal

Certificates auto-renew every 12 hours. To manually renew:
```bash
docker compose -f docker-compose.prod.yml exec certbot certbot renew
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### Clear Redis cache
```bash
# Clear all cache
docker compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL

# Clear specific pattern
docker compose -f docker-compose.prod.yml exec redis redis-cli --scan --pattern "statement:*" | xargs docker compose -f docker-compose.prod.yml exec redis redis-cli DEL
```

### Backup database
```bash
# Create backup
docker compose -f docker-compose.prod.yml exec db pg_dump -U mattilda_user mattilda_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker compose -f docker-compose.prod.yml exec -T db psql -U mattilda_user mattilda_prod < backup_20260118_120000.sql
```

## Monitoring

### Check service health
```bash
# Database
docker compose -f docker-compose.prod.yml exec db pg_isready -U mattilda_user

# Redis
docker compose -f docker-compose.prod.yml exec redis redis-cli ping

# Backend
curl https://yourdomain.com/api/health
```

### Monitor resource usage
```bash
docker stats
```

## Troubleshooting

### SSL certificate issues
If certificate generation fails:
1. Ensure your domain points to the server
2. Check ports 80 and 443 are accessible
3. Review certbot logs: `docker compose -f docker-compose.prod.yml logs certbot`

### Backend not starting
1. Check logs: `docker compose -f docker-compose.prod.yml logs backend`
2. Verify database is healthy: `docker compose -f docker-compose.prod.yml ps db`
3. Check environment variables in `.env.prod`

### Cache not working
1. Check Redis is running: `docker compose -f docker-compose.prod.yml ps redis`
2. Test Redis connection: `docker compose -f docker-compose.prod.yml exec redis redis-cli ping`
3. Review backend logs for cache errors

## Scaling

### Increase backend workers
Edit `backend/Dockerfile.prod` and change:
```dockerfile
CMD ["sh", "-c", "alembic upgrade head && gunicorn app.main:app --workers 8 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"]
```

### Add Redis persistence
Redis is already configured with AOF (Append Only File) persistence.

### Database connection pooling
Adjust in `backend/app/db.py` if needed.

## Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| Server | Uvicorn (reload) | Gunicorn (4 workers) |
| Frontend | Vite dev server | Nginx static files |
| SSL | None | Let's Encrypt |
| Cache | Redis | Redis |
| Logs | Console | Docker logs |
| Database | Local volume | Named volume |

## Support

For issues or questions, please open an issue on the repository.

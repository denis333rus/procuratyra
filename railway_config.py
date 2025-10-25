# Railway deployment configuration
# This file contains additional configuration for Railway deployment

# Static files configuration
STATIC_FOLDER = 'static'
TEMPLATE_FOLDER = 'templates'

# Security headers for production
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'"
}

# Database connection pool settings for PostgreSQL
DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 10
DB_POOL_TIMEOUT = 30
DB_POOL_RECYCLE = 3600

# File upload limits
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}

# Session configuration
PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
SESSION_COOKIE_NAME = 'procuratyra_session'

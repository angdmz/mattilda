from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declared_attr


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps to models."""
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime, nullable=False, default=datetime.utcnow)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class SoftDeleteMixin:
    """Mixin that adds soft delete functionality via revoked_at field."""
    
    @declared_attr
    def revoked_at(cls):
        return Column(DateTime, nullable=True, default=None)
    
    @property
    def is_revoked(self):
        return self.revoked_at is not None
    
    def soft_delete(self):
        self.revoked_at = datetime.utcnow()
    
    def restore(self):
        self.revoked_at = None

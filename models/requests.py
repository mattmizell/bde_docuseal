"""
Request Models for DocuSeal Service
Pydantic models for API request validation
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, EmailStr

class DocumentInitiateRequest(BaseModel):
    """Request to initiate document signing"""
    template_id: str
    customer_email: EmailStr
    customer_name: str
    form_data: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "template_id": "tmpl_123456",
                "customer_email": "customer@example.com",
                "customer_name": "John Doe",
                "form_data": {
                    "company_name": "Acme Corp",
                    "contact_phone": "555-0123",
                    "address": "123 Main St"
                }
            }
        }

class DocumentStatusRequest(BaseModel):
    """Request to check document status"""
    submission_id: str
    
    class Config:
        schema_extra = {
            "example": {
                "submission_id": "sub_123456"
            }
        }

class WebhookEventRequest(BaseModel):
    """DocuSeal webhook event payload"""
    event_type: str
    submission_id: str
    submitter_email: Optional[str] = None
    document_url: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "event_type": "form.completed",
                "submission_id": "sub_123456",
                "submitter_email": "customer@example.com",
                "document_url": "https://docuseal.co/d/123456",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class TemplateCreateRequest(BaseModel):
    """Request to create a new template (if needed)"""
    name: str
    description: Optional[str] = None
    fields: List[Dict[str, Any]] = []
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Customer Setup Agreement",
                "description": "Standard customer onboarding document",
                "fields": [
                    {
                        "name": "customer_name",
                        "type": "text",
                        "required": True,
                        "label": "Customer Name"
                    },
                    {
                        "name": "company_name",
                        "type": "text",
                        "required": True,
                        "label": "Company Name"
                    }
                ]
            }
        }

class ReminderRequest(BaseModel):
    """Request to send reminder email"""
    submission_id: str
    recipient_email: EmailStr
    
    class Config:
        schema_extra = {
            "example": {
                "submission_id": "sub_123456",
                "recipient_email": "customer@example.com"
            }
        }
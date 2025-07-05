#!/usr/bin/env python3
"""
BDE DocuSeal Service - External E-Signature Service

Dedicated microservice for DocuSeal integration.
Handles all e-signature workflows as a separate service.
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import uvicorn

from services.docuseal_client import DocuSealClient
from services.email_service import EmailService
from models.requests import (
    DocumentInitiateRequest,
    WebhookEventRequest,
    DocumentStatusRequest
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="BDE DocuSeal Service",
    description="External document signing service with DocuSeal integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
docuseal_client = DocuSealClient(
    base_url=os.getenv('DOCUSEAL_URL', 'https://docuseal.co'),
    api_token=os.getenv('DOCUSEAL_API_TOKEN', '')
)

email_service = EmailService(
    smtp_host=os.getenv('SMTP_HOST', 'smtp.gmail.com'),
    smtp_port=int(os.getenv('SMTP_PORT', '587')),
    smtp_username=os.getenv('SMTP_USERNAME', 'transaction.coordinator.agent@gmail.com'),
    smtp_password=os.getenv('SMTP_PASSWORD', 'xmvi xvso zblo oewe'),
    from_email=os.getenv('FROM_EMAIL', 'transaction.coordinator.agent@gmail.com')
)

# =====================================================
# HEALTH CHECK AND STATUS
# =====================================================

@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "service": "BDE DocuSeal Service",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "description": "External document signing service"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    
    # Test DocuSeal connection
    docuseal_status = await docuseal_client.health_check()
    
    # Test email service
    email_status = email_service.test_connection()
    
    return {
        "status": "healthy" if all([
            docuseal_status.get("status") == "healthy",
            email_status.get("status") == "healthy"
        ]) else "degraded",
        "services": {
            "docuseal": docuseal_status,
            "email": email_status
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# =====================================================
# DOCUMENT SIGNING ENDPOINTS
# =====================================================

@app.post("/api/v1/documents/initiate")
async def initiate_document_signing(
    request_data: DocumentInitiateRequest,
    background_tasks: BackgroundTasks
):
    """Initiate document signing workflow"""
    
    try:
        # Create DocuSeal submission
        submission_result = await docuseal_client.create_submission(
            template_id=request_data.template_id,
            customer_email=request_data.customer_email,
            customer_name=request_data.customer_name,
            pre_filled_data=request_data.form_data
        )
        
        if not submission_result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=f"DocuSeal submission failed: {submission_result.get('error')}"
            )
        
        logger.info(f"✅ Document signing initiated: {submission_result['submission_id']}")
        
        return {
            "submission_id": submission_result["submission_id"],
            "signing_url": submission_result.get("signing_url"),
            "status": "initiated",
            "message": f"Document sent to {request_data.customer_email}"
        }
        
    except Exception as e:
        logger.error(f"❌ Document initiation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate document: {str(e)}")

@app.get("/api/v1/documents/{submission_id}/status")
async def get_document_status(submission_id: str):
    """Get document status from DocuSeal"""
    
    try:
        status = await docuseal_client.get_submission_status(submission_id)
        
        return {
            "submission_id": submission_id,
            "status": status.get("status"),
            "completed_at": status.get("completed_at"),
            "document_url": status.get("document_url"),
            "signer_email": status.get("signer_email")
        }
        
    except Exception as e:
        logger.error(f"❌ Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@app.get("/api/v1/documents/{submission_id}/download")
async def download_document(submission_id: str):
    """Download completed document"""
    
    try:
        document_data = await docuseal_client.download_document(submission_id)
        
        if not document_data:
            raise HTTPException(status_code=404, detail="Document not found or not completed")
        
        return {
            "submission_id": submission_id,
            "download_url": document_data.get("download_url"),
            "filename": document_data.get("filename"),
            "size_bytes": document_data.get("size_bytes")
        }
        
    except Exception as e:
        logger.error(f"❌ Download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download: {str(e)}")

# =====================================================
# WEBHOOK ENDPOINTS
# =====================================================

@app.post("/api/v1/webhooks/docuseal")
async def handle_docuseal_webhook(
    webhook_data: WebhookEventRequest,
    background_tasks: BackgroundTasks
):
    """Handle DocuSeal webhook events"""
    
    try:
        logger.info(f"📥 DocuSeal webhook received: {webhook_data.event_type}")
        
        # Process webhook event
        if webhook_data.event_type == "form.completed":
            # Send completion notification
            background_tasks.add_task(
                send_completion_notification,
                webhook_data.submission_id,
                webhook_data.submitter_email
            )
            
        elif webhook_data.event_type == "form.viewed":
            logger.info(f"📖 Document viewed: {webhook_data.submission_id}")
            
        elif webhook_data.event_type == "form.started":
            logger.info(f"🖊️ Document signing started: {webhook_data.submission_id}")
        
        logger.info(f"✅ Webhook processed: {webhook_data.event_type}")
        
        return {"status": "processed"}
        
    except Exception as e:
        logger.error(f"❌ Webhook processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

# =====================================================
# TEMPLATE MANAGEMENT
# =====================================================

@app.get("/api/v1/templates")
async def list_templates():
    """List available DocuSeal templates"""
    
    try:
        templates = await docuseal_client.list_templates()
        
        return {
            "templates": templates,
            "count": len(templates)
        }
        
    except Exception as e:
        logger.error(f"❌ Template listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")

@app.get("/api/v1/templates/{template_id}")
async def get_template_details(template_id: str):
    """Get template details and fields"""
    
    try:
        template = await docuseal_client.get_template(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "template": template
        }
        
    except Exception as e:
        logger.error(f"❌ Template lookup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")

# =====================================================
# BACKGROUND TASKS
# =====================================================

async def send_completion_notification(submission_id: str, signer_email: str):
    """Send notification when document is completed"""
    
    try:
        logger.info(f"📧 Sending completion notification for {submission_id} to {signer_email}")
        
        # Get document details
        status = await docuseal_client.get_submission_status(submission_id)
        
        # Send email notification
        await email_service.send_completion_email(
            recipient_email=signer_email,
            submission_id=submission_id,
            document_url=status.get("document_url")
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to send completion notification: {str(e)}")

# =====================================================
# APPLICATION STARTUP
# =====================================================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    
    logger.info("🚀 BDE DocuSeal Service starting up...")
    
    # Test connections
    health = await health_check()
    
    if health["status"] == "healthy":
        logger.info("✅ All services connected successfully")
    else:
        logger.warning("⚠️ Some services may not be available")
        logger.warning(f"Service status: {health['services']}")
    
    logger.info("🎉 BDE DocuSeal Service ready!")

if __name__ == "__main__":
    # For local development
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
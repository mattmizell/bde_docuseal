"""
DocuSeal API Client
Professional e-signature integration service
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class DocuSealClient:
    """DocuSeal API integration client"""
    
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.timeout = 30.0
        
        # Validate configuration
        if not self.api_token:
            logger.warning("⚠️ DocuSeal API token not configured")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check DocuSeal service health"""
        
        if not self.api_token:
            return {
                "status": "error",
                "error": "API token not configured"
            }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/templates",
                    headers={"X-Auth-Token": self.api_token}
                )
                
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                        "api_version": response.headers.get("X-API-Version", "unknown")
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except httpx.TimeoutException:
            return {
                "status": "error",
                "error": "Connection timeout"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def create_submission(
        self,
        template_id: str,
        customer_email: str,
        customer_name: str,
        pre_filled_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new document submission"""
        
        try:
            payload = {
                "template_id": template_id,
                "send_email": True,
                "submitters": [
                    {
                        "role": "Customer",
                        "email": customer_email,
                        "name": customer_name
                    }
                ]
            }
            
            # Add pre-filled data if provided
            if pre_filled_data:
                payload["fields"] = pre_filled_data
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/submissions",
                    headers={
                        "X-Auth-Token": self.api_token,
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                if response.status_code == 201:
                    result = response.json()
                    
                    return {
                        "success": True,
                        "submission_id": result.get("id"),
                        "signing_url": result.get("submitters", [{}])[0].get("embed_src"),
                        "email_sent": True
                    }
                else:
                    logger.error(f"❌ DocuSeal submission failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except httpx.TimeoutException:
            logger.error("❌ DocuSeal API timeout")
            return {
                "success": False,
                "error": "DocuSeal API timeout"
            }
        except Exception as e:
            logger.error(f"❌ DocuSeal submission error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_submission_status(self, submission_id: str) -> Dict[str, Any]:
        """Get submission status and details"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/submissions/{submission_id}",
                    headers={"X-Auth-Token": self.api_token}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    return {
                        "status": result.get("status"),
                        "completed_at": result.get("completed_at"),
                        "document_url": result.get("documents", [{}])[0].get("url"),
                        "signer_email": result.get("submitters", [{}])[0].get("email"),
                        "template_name": result.get("template", {}).get("name")
                    }
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"DocuSeal API error: {response.text}"
                    )
                    
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="DocuSeal API timeout")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DocuSeal error: {str(e)}")
    
    async def download_document(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Download completed document"""
        
        try:
            # First get submission details
            status = await self.get_submission_status(submission_id)
            
            if status.get("status") != "completed":
                return None
            
            document_url = status.get("document_url")
            if not document_url:
                return None
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    document_url,
                    headers={"X-Auth-Token": self.api_token}
                )
                
                if response.status_code == 200:
                    return {
                        "download_url": document_url,
                        "filename": f"document_{submission_id}.pdf",
                        "size_bytes": len(response.content),
                        "content_type": response.headers.get("content-type", "application/pdf")
                    }
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Document download error: {e}")
            return None
    
    async def list_templates(self) -> List[Dict[str, Any]]:
        """List available document templates"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/templates",
                    headers={"X-Auth-Token": self.api_token}
                )
                
                if response.status_code == 200:
                    templates = response.json()
                    
                    return [
                        {
                            "id": template.get("id"),
                            "name": template.get("name"),
                            "description": template.get("description"),
                            "fields_count": len(template.get("schema", [])),
                            "created_at": template.get("created_at")
                        }
                        for template in templates
                    ]
                else:
                    logger.error(f"❌ Template listing failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Template listing error: {e}")
            return []
    
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template details and field schema"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/templates/{template_id}",
                    headers={"X-Auth-Token": self.api_token}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Template lookup error: {e}")
            return None
    
    async def cancel_submission(self, submission_id: str) -> bool:
        """Cancel a pending submission"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/api/submissions/{submission_id}",
                    headers={"X-Auth-Token": self.api_token}
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"❌ Submission cancellation error: {e}")
            return False
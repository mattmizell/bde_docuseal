"""
Email Service for DocuSeal Integration
Handles all email notifications for document signing workflows
"""

import asyncio
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for document signing notifications"""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        from_email: str
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email
    
    def test_connection(self) -> Dict[str, Any]:
        """Test SMTP connection"""
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                
            return {
                "status": "healthy",
                "smtp_host": self.smtp_host,
                "smtp_port": self.smtp_port
            }
            
        except Exception as e:
            logger.error(f"❌ SMTP connection failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def send_completion_email(
        self,
        recipient_email: str,
        submission_id: str,
        document_url: Optional[str] = None
    ) -> bool:
        """Send document completion notification"""
        
        try:
            subject = "✅ Document Signing Completed - BDE Energy"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">✅ Document Signing Completed</h1>
                        <p style="margin: 10px 0 0 0; opacity: 0.9;">Better Day Energy</p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                        <h2 style="color: #495057; margin-top: 0;">Great News!</h2>
                        
                        <p>Your document has been successfully signed and completed.</p>
                        
                        <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745; margin: 20px 0;">
                            <h3 style="margin: 0 0 10px 0; color: #28a745;">Document Details:</h3>
                            <p style="margin: 5px 0;"><strong>Submission ID:</strong> {submission_id}</p>
                            <p style="margin: 5px 0;"><strong>Completed At:</strong> {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}</p>
                            <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: #28a745; font-weight: bold;">Completed</span></p>
                        </div>
                        
                        {f'''
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{document_url}" 
                               style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                                📄 Download Signed Document
                            </a>
                        </div>
                        ''' if document_url else ''}
                        
                        <div style="background: #e7f3ff; padding: 15px; border-radius: 6px; margin: 20px 0;">
                            <p style="margin: 0; font-size: 14px;">
                                <strong>Next Steps:</strong> Your signed document is now complete. 
                                A copy has been securely stored and our team will process your request shortly.
                            </p>
                        </div>
                        
                        <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                        
                        <p style="margin: 0; font-size: 12px; color: #6c757d; text-align: center;">
                            This email was sent by Better Day Energy's automated document system.<br>
                            If you have questions, please contact our support team.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_body = f"""
            Document Signing Completed - Better Day Energy
            
            Great News! Your document has been successfully signed and completed.
            
            Document Details:
            - Submission ID: {submission_id}
            - Completed At: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}
            - Status: Completed
            
            {"Download: " + document_url if document_url else ""}
            
            Next Steps: Your signed document is now complete. A copy has been securely stored 
            and our team will process your request shortly.
            
            This email was sent by Better Day Energy's automated document system.
            If you have questions, please contact our support team.
            """
            
            return await self._send_email(
                recipient_email=recipient_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send completion email: {e}")
            return False
    
    async def send_reminder_email(
        self,
        recipient_email: str,
        submission_id: str,
        signing_url: str,
        days_pending: int
    ) -> bool:
        """Send reminder for pending document signing"""
        
        try:
            subject = f"⏰ Reminder: Document Signing Pending - BDE Energy"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: #333; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">⏰ Document Signing Reminder</h1>
                        <p style="margin: 10px 0 0 0; opacity: 0.8;">Better Day Energy</p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                        <h2 style="color: #495057; margin-top: 0;">Action Required</h2>
                        
                        <p>You have a document waiting for your signature. This document has been pending for <strong>{days_pending} days</strong>.</p>
                        
                        <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 20px 0;">
                            <h3 style="margin: 0 0 10px 0; color: #ffc107;">Document Details:</h3>
                            <p style="margin: 5px 0;"><strong>Submission ID:</strong> {submission_id}</p>
                            <p style="margin: 5px 0;"><strong>Days Pending:</strong> {days_pending}</p>
                            <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: #ffc107; font-weight: bold;">Waiting for Signature</span></p>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{signing_url}" 
                               style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; font-size: 16px;">
                                🖊️ Sign Document Now
                            </a>
                        </div>
                        
                        <div style="background: #fff3cd; padding: 15px; border-radius: 6px; margin: 20px 0; border: 1px solid #ffeaa7;">
                            <p style="margin: 0; font-size: 14px;">
                                <strong>Important:</strong> Please complete the signing process to avoid delays in processing your request.
                            </p>
                        </div>
                        
                        <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                        
                        <p style="margin: 0; font-size: 12px; color: #6c757d; text-align: center;">
                            This reminder was sent by Better Day Energy's automated document system.<br>
                            If you have questions, please contact our support team.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_body = f"""
            Document Signing Reminder - Better Day Energy
            
            Action Required: You have a document waiting for your signature.
            This document has been pending for {days_pending} days.
            
            Document Details:
            - Submission ID: {submission_id}
            - Days Pending: {days_pending}
            - Status: Waiting for Signature
            
            Sign Document: {signing_url}
            
            Important: Please complete the signing process to avoid delays in processing your request.
            
            This reminder was sent by Better Day Energy's automated document system.
            If you have questions, please contact our support team.
            """
            
            return await self._send_email(
                recipient_email=recipient_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send reminder email: {e}")
            return False
    
    async def _send_email(
        self,
        recipient_email: str,
        subject: str,
        html_body: str,
        text_body: str
    ) -> bool:
        """Send email with HTML and text versions"""
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = recipient_email
            
            # Add text and HTML parts
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {recipient_email}: {e}")
            return False
# BDE DocuSeal Service

External document signing service for Better Day Energy using DocuSeal integration.

## Overview

This is a dedicated microservice that handles all e-signature workflows through DocuSeal. It operates independently from the main sales portal and communicates via REST API.

## Architecture

- **FastAPI**: Modern Python web framework
- **DocuSeal Integration**: Professional e-signature service
- **Email Notifications**: Automated completion and reminder emails
- **Webhook Support**: Real-time status updates from DocuSeal

## Features

- ✅ Document initiation and template management
- ✅ Real-time status tracking
- ✅ Webhook event processing
- ✅ Email notifications (completion/reminders)
- ✅ Document download and storage
- ✅ Health monitoring and logging

## API Endpoints

### Document Management
- `POST /api/v1/documents/initiate` - Start document signing
- `GET /api/v1/documents/{id}/status` - Check signing status
- `GET /api/v1/documents/{id}/download` - Download completed document

### Templates
- `GET /api/v1/templates` - List available templates
- `GET /api/v1/templates/{id}` - Get template details

### Webhooks
- `POST /api/v1/webhooks/docuseal` - DocuSeal event webhooks

### Health
- `GET /health` - Service health check
- `GET /` - Service information

## Environment Configuration

```env
# DocuSeal Configuration
DOCUSEAL_URL=https://docuseal.co
DOCUSEAL_API_TOKEN=your_api_token_here

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=transaction.coordinator.agent@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=transaction.coordinator.agent@gmail.com

# Service Configuration
PORT=8001
```

## Deployment

### Render.com

1. Connect Git repository to Render
2. Create new Web Service
3. Use `render.yaml` configuration
4. Set environment variables in dashboard
5. Deploy

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your credentials

# Run service
python main.py
```

Service runs on `http://localhost:8001`

## Integration

The main sales portal communicates with this service via HTTP:

```python
# Example: Initiate document signing
async def initiate_signing(customer_email, template_id, form_data):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{DOCUSEAL_SERVICE_URL}/api/v1/documents/initiate",
            json={
                "template_id": template_id,
                "customer_email": customer_email,
                "customer_name": "John Doe",
                "form_data": form_data
            }
        )
        return response.json()
```

## Monitoring

- Health check: `GET /health`
- Logs: Structured JSON logging
- Metrics: Response times and success rates
- Alerts: Failed document processing

## Security

- API token authentication with DocuSeal
- HTTPS only in production
- Email credentials via secure environment variables
- CORS configured for specific origins

## Production URLs

- **Service**: `https://bde-docuseal-service.onrender.com`
- **Health**: `https://bde-docuseal-service.onrender.com/health`
- **Docs**: `https://bde-docuseal-service.onrender.com/docs`
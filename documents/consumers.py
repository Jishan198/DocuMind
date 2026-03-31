import json
import structlog
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from tenants.models import Membership

logger = structlog.get_logger(__name__)


class DocumentProgressConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer that pushes real-time document processing updates.
    
    Flow:
    1. Client connects with org_id in URL
    2. Consumer verifies user is a member of that org
    3. Consumer joins org-specific channel group
    4. Celery task broadcasts progress → channel layer → this consumer → client
    """

    async def connect(self):
        self.org_id = self.scope['url_route']['kwargs']['org_id']
        self.group_name = f'document_progress_{self.org_id}'
        user = self.scope.get('user')

        # Reject unauthenticated connections
        if not user or user.is_anonymous:
            await self.close()
            return

        # Verify user belongs to this organization
        is_member = await self._check_membership(user, self.org_id)
        if not is_member:
            await self.close()
            return

        # Join the org's progress group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        logger.info("ws_connected", org_id=self.org_id, user=str(user))

    async def disconnect(self, close_code):
        # Leave the group on disconnect
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def document_progress(self, event):
        """
        Handler for messages sent to the group.
        Called when Celery task broadcasts via channel layer.
        Event format: {
            'type': 'document.progress',
            'document_id': '...',
            'title': '...',
            'status': 'PROCESSING|READY|FAILED',
            'stage': 'extracting|chunking|embedding|saving|complete|failed',
            'progress': 0-100,
            'message': 'Human readable status...',
            'chunk_count': 0,
        }
        """
        await self.send_json({
            'document_id': event['document_id'],
            'title': event.get('title', ''),
            'status': event['status'],
            'stage': event.get('stage', ''),
            'progress': event.get('progress', 0),
            'message': event.get('message', ''),
            'chunk_count': event.get('chunk_count', 0),
        })

    @database_sync_to_async
    def _check_membership(self, user, org_id):
        return Membership.objects.filter(
            user=user,
            organization_id=org_id,
            is_active=True
        ).exists()

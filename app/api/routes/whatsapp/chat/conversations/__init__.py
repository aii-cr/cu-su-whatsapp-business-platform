"""WhatsApp chat conversations routes package."""

from fastapi import APIRouter

from .create_conversation import router as create_conversation_router
from .start_conversation import router as start_conversation_router
from .list_conversations import router as list_conversations_router
from .get_conversation import router as get_conversation_router
from .get_conversation_with_messages import router as get_conversation_with_messages_router
from .update_conversation import router as update_conversation_router
from .delete_conversation import router as delete_conversation_router
from .get_stats import router as get_stats_router
from .close_conversation import router as close_conversation_router
from .transfer_conversation import router as transfer_conversation_router
from .participants.add_participant import router as add_participant_router
from .participants.remove_participant import router as remove_participant_router
from .participants.change_participant_role import router as change_participant_role_router
from .participants.get_participants import router as get_participants_router
from .participants.get_participant_history import router as get_participant_history_router
from .history.get_history import router as get_history_router
from .history.export_history_pdf import router as export_history_pdf_router
from .history.add_note import router as add_note_router
from .tags.get_conversation_tags import router as get_conversation_tags_router
from .tags.assign_tags import router as assign_tags_router
from .tags.unassign_tags import router as unassign_tags_router
from .archive.archive_conversation import router as archive_conversation_router
from .archive.restore_conversation import router as restore_conversation_router
from .archive.purge_conversation import router as purge_conversation_router

# Create main conversations router
router = APIRouter(prefix="/conversations", tags=["Conversations"])

# Include all conversation endpoint routers
router.include_router(create_conversation_router)
router.include_router(start_conversation_router)
router.include_router(list_conversations_router)
router.include_router(get_conversation_router)
router.include_router(get_conversation_with_messages_router)
router.include_router(update_conversation_router)
router.include_router(delete_conversation_router)
router.include_router(get_stats_router)
router.include_router(close_conversation_router)
router.include_router(transfer_conversation_router) 
router.include_router(add_participant_router)
router.include_router(remove_participant_router)
router.include_router(change_participant_role_router)
router.include_router(get_participants_router)
router.include_router(get_participant_history_router)
router.include_router(get_history_router)
router.include_router(export_history_pdf_router)
router.include_router(add_note_router)
router.include_router(get_conversation_tags_router)
router.include_router(assign_tags_router)
router.include_router(unassign_tags_router)
router.include_router(archive_conversation_router)
router.include_router(restore_conversation_router)
router.include_router(purge_conversation_router)
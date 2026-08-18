import pytest
from app.database.models import User, Conversation
from app.services.conversation_service import ConversationService
from app.services.message_router import MessageRouter

@pytest.mark.asyncio
async def test_strict_reply_target_isolation(in_memory_db, mock_redis, mock_bot):
    """
    CRITICAL TEST SCENARIO:
    Owner has conversations A, B and C.
    Owner locks reply target on B -> Dispatches message -> Must route ONLY to B.
    Owner locks reply target on A -> Dispatches message -> Must route ONLY to A.
    """
    owner = User(telegram_id=100)
    user_a = User(telegram_id=200)
    user_b = User(telegram_id=300)
    user_c = User(telegram_id=400)
    in_memory_db.add_all([owner, user_a, user_b, user_c])
    await in_memory_db.flush()

    conv_service = ConversationService(in_memory_db)
    conv_a = await conv_service.initiate_or_resume(owner, user_a)
    conv_b = await conv_service.initiate_or_resume(owner, user_b)
    conv_c = await conv_service.initiate_or_resume(owner, user_c)

    router = MessageRouter(in_memory_db, mock_redis, mock_bot)

    # 1. Simulate incoming anonymous message from user B to Owner
    msg_from_b = await router.dispatch_anonymous_to_owner(
        conversation_id=conv_b.id,
        sender=user_b,
        owner=owner,
        content_type="text",
        payload={"text": "Hello from B"}
    )

    # 2. Owner clicks reply on message from B
    mock_redis.get.return_value = str(msg_from_b.id).encode("utf-8")

    # 3. Owner dispatches reply
    reply_to_b = await router.dispatch_owner_reply(
        owner=owner,
        content_type="text",
        payload={"text": "Replying exclusively to B"}
    )
    assert reply_to_b.conversation_id == conv_b.id
    assert reply_to_b.recipient_user_id == user_b.id
    mock_bot.send_message.assert_called_with(
        chat_id=user_b.telegram_id,
        text="📬 **پاسخ جدید از طرف مخاطب:**\n\nReplying exclusively to B",
        reply_markup=None
    )

    # 4. Now simulate incoming from A and switch active reply target
    msg_from_a = await router.dispatch_anonymous_to_owner(
        conversation_id=conv_a.id,
        sender=user_a,
        owner=owner,
        content_type="text",
        payload={"text": "Hello from A"}
    )
    mock_redis.get.return_value = str(msg_from_a.id).encode("utf-8")

    # 5. Owner dispatches reply -> Must reach A and ONLY A
    reply_to_a = await router.dispatch_owner_reply(
        owner=owner,
        content_type="text",
        payload={"text": "Replying exclusively to A"}
    )
    assert reply_to_a.conversation_id == conv_a.id
    assert reply_to_a.recipient_user_id == user_a.id
    mock_bot.send_message.assert_called_with(
        chat_id=user_a.telegram_id,
        text="📬 **پاسخ جدید از طرف مخاطب:**\n\nReplying exclusively to A",
        reply_markup=None
    )
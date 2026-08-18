import pytest
from app.database.models import User, Channel, ChannelMessage
from app.services.seen_tracker import SeenTrackerService

@pytest.mark.asyncio
async def test_seen_button_idempotency(in_memory_db, mock_redis):
    author = User(telegram_id=901)
    viewer = User(telegram_id=902)
    in_memory_db.add_all([author, viewer])
    await in_memory_db.flush()

    channel = Channel(telegram_channel_id=-100123456789, title="Test Channel")
    in_memory_db.add(channel)
    await in_memory_db.flush()

    msg = ChannelMessage(channel_id=channel.id, author_id=author.id, telegram_message_id=555)
    in_memory_db.add(msg)
    await in_memory_db.flush()

    tracker = SeenTrackerService(in_memory_db, mock_redis)

    # First click -> Count 1, is_new True
    is_new, count, target_author = await tracker.register_seen_event(-100123456789, 555, viewer.telegram_id)
    assert is_new is True
    assert count == 1
    assert target_author.telegram_id == author.telegram_id

    # Second click from same user -> Count 1, is_new False
    is_new2, count2, target_author2 = await tracker.register_seen_event(-100123456789, 555, viewer.telegram_id)
    assert is_new2 is False
    assert count2 == 1
import pytest
from app.database.models import User, Channel, ChannelLink
from app.services.channel_publisher import ChannelPublisherService

@pytest.mark.asyncio
async def test_publish_anonymous_post(in_memory_db, mock_bot):
    author = User(telegram_id=888, nickname="Tester")
    channel = Channel(telegram_channel_id=-100987654321, title="Test Channel")
    in_memory_db.add_all([author, channel])
    await in_memory_db.flush()

    link = ChannelLink(
        channel_id=channel.id,
        token="c_testchannel",
        template="{message}\n\n{nickname}",
        show_seen_button=True
    )
    in_memory_db.add(link)
    await in_memory_db.flush()

    publisher = ChannelPublisherService(in_memory_db, mock_bot)
    msg_id = await publisher.publish_anonymous_post(
        channel=channel,
        channel_link=link,
        author=author,
        content_type="text",
        payload={"text": "Hello channel"}
    )

    assert msg_id == 99999
    mock_bot.send_message.assert_called_once()

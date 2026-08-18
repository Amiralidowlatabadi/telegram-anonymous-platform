import pytest
from app.database.models import User
from app.services.link_service import LinkService
from app.core.exceptions import ValidationError, SlugCollisionError

@pytest.mark.asyncio
async def test_personal_link_lifecycle(in_memory_db):
    user = User(telegram_id=1001)
    in_memory_db.add(user)
    await in_memory_db.flush()

    link_service = LinkService(in_memory_db)
    link1 = await link_service.get_or_create_personal_link(user)
    assert link1.token.startswith("p_")
    assert link1.is_active is True

    link2 = await link_service.regenerate_personal_link(user)
    assert link2.token.startswith("p_")
    assert link2.token != link1.token
    assert link1.is_active is False

@pytest.mark.asyncio
async def test_custom_slug_rules(in_memory_db):
    user = User(telegram_id=1002)
    in_memory_db.add(user)
    await in_memory_db.flush()

    link_service = LinkService(in_memory_db)
    
    # Invalid length
    with pytest.raises(ValidationError):
        await link_service.set_custom_personal_slug(user, "ab")

    # Reserved slug
    with pytest.raises(ValidationError):
        await link_service.set_custom_personal_slug(user, "admin")

    # Valid slug
    custom_link = await link_service.set_custom_personal_slug(user, "shadow_hunter")
    assert custom_link.token == "p_shadow_hunter"
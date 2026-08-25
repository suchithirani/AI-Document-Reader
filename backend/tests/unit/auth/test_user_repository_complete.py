import pytest
from bson import ObjectId

from app.common.utils.datetime import utc_now
from app.modules.auth.repository import UserRepository


@pytest.mark.asyncio
async def test_user_repository_complete_crud_and_lookups(mock_db):
    repo = UserRepository(mock_db)
    user_data = {
        "email": "full_test@example.com",
        "name": "Full Test User",
        "phone_number": "+1234567890",
        "google_id": "google_123",
        "password_hash": "hash123",
        "is_active": True,
        "is_verified": False,
        "phone_verified": False,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }

    # 1. Create User
    created = await repo.create_user(user_data)
    user_id = str(created.id)
    assert created.email == "full_test@example.com"

    # 2. Lookups (Found)
    assert (await repo.get_by_email("full_test@example.com")) is not None
    assert (await repo.get_by_id(user_id)) is not None
    assert (await repo.get_by_phone("+1234567890")) is not None
    assert (await repo.get_by_google_id("google_123")) is not None

    # 3. Lookups (Not Found)
    assert (await repo.get_by_email("nonexistent@example.com")) is None
    assert (await repo.get_by_id(str(ObjectId()))) is None
    assert (await repo.get_by_phone("+9999999999")) is None
    assert (await repo.get_by_google_id("google_nonexistent")) is None

    # 4. Updates (Found)
    u_login = await repo.update_last_login(user_id)
    assert u_login is not None

    u_pass = await repo.update_password(user_id, "new_hash")
    assert u_pass is not None

    u_v_email = await repo.verify_email(user_id)
    assert u_v_email is not None and u_v_email.is_verified is True

    u_v_phone = await repo.verify_phone(user_id)
    assert u_v_phone is not None and u_v_phone.phone_verified is True

    u_pic = await repo.update_profile_picture(user_id, "https://example.com/avatar.png")
    assert u_pic is not None

    u_deact = await repo.deactivate_user(user_id)
    assert u_deact is not None and u_deact.is_active is False

    # 5. Updates (Not Found)
    fake_id = str(ObjectId())
    assert (await repo.update_last_login(fake_id)) is None
    assert (await repo.update_password(fake_id, "h")) is None
    assert (await repo.verify_email(fake_id)) is None
    assert (await repo.verify_phone(fake_id)) is None
    assert (await repo.update_profile_picture(fake_id, "p")) is None
    assert (await repo.deactivate_user(fake_id)) is None

    # 6. Revoke all user tokens
    revoked_count = await repo.revoke_all_user_tokens(user_id)
    assert isinstance(revoked_count, int)

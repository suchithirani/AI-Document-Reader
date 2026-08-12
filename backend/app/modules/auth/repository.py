from app.modules.auth.model import User
from pymongo import ReturnDocument
from app.common.utils.datetime import utc_now
from app.common.constants import CollectionName
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db[CollectionName.USERS.value])

    async def create_user(self, user: dict)-> User:
        created = await self.create(user)
        return User.model_validate(created)

    async def get_by_email(self, email: str):
        user = await self.get_one({"email": email})

        if user is None:
            return None

        return User.model_validate(user)

    async def get_by_id(self, user_id: str) -> User | None:
        user = await super().get_by_id(user_id)

        if user is None:
            return None

        return User.model_validate(user)
    async def get_by_phone(self, phone_number: str) -> User | None:
        user = await self.get_one({"phone_number": phone_number})

        if user is None:
            return None

        return User.model_validate(user)

    async def get_by_google_id(self, google_id: str) -> User | None:
        user = await self.get_one({"google_id": google_id})

        if user is None:
            return None

        return User.model_validate(user)

    async def update_last_login(self, user_id: str) -> User | None:
        user = await self.update(
            user_id,
            {
                "last_login": utc_now(),
                "updated_at": utc_now(),
            },
        )

        if user is None:
            return None

        return User.model_validate(user)

    async def update_password(self, user_id: str, password_hash: str) -> User | None:
        user = await self.update(
            user_id,
            {
                "password_hash": password_hash,
                "updated_at": utc_now(),
            },
        )

        if user is None:
            return None

        return User.model_validate(user)

    async def verify_email(self, user_id: str):
        user = await self.update(
            user_id,
            {
                "is_verified": True,
                "updated_at": utc_now(),
            },
        )
        if user is None:
            return None
        return User.model_validate(user)

    async def verify_phone(self, user_id: str):
        user = await self.update(
            user_id,
            {
                "phone_verified": True,
                "updated_at": utc_now(),
            },
        )

        if user is None:
            return None

        return User.model_validate(user)
    
    async def update_profile_picture(self, user_id: str, profile_picture: str):
        user = await self.update(
            user_id,
            {
                "profile_picture": profile_picture,
                "updated_at": utc_now(),
            },
        )

        if user is None:
            return None

        return User.model_validate(user)

    async def deactivate_user(self, user_id: str):
        user = await self.update(
            user_id,
            {
                "is_active": False,
                "updated_at": utc_now(),
            },
        )

        if user is None:
            return None

        return User.model_validate(user)

    async def revoke_all_user_tokens(
        self,
        user_id: str,
    ) -> int:

        result = await self.collection.update_many(
            {
                "user_id": user_id,
                "revoked": False,
            },
            {
                "$set": {
                    "revoked": True,
                    "updated_at": utc_now(),
                }
            },
        )

        return result.modified_count
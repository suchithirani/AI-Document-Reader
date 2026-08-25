from app.common.constants import CollectionName
from app.common.utils.datetime import utc_now
from app.modules.auth.refresh_models import RefreshToken
from app.repositories.base_repository import BaseRepository


class RefreshTokenRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db[CollectionName.REFRESH_TOKENS.value])

    async def create_refresh_token(
        self,
        token: dict,
    ) -> RefreshToken:
        created = await self.create(token)
        return RefreshToken.model_validate(created)

    async def get_by_token_hash(
    self,
    token_hash: str,
):
      document = await self.get_one(
          {"token_hash": token_hash}
      )

      return (
          RefreshToken.model_validate(document)
          if document
          else None
      )

    async def revoke_refresh_token(
        self,
        token_hash: str,
    ) -> RefreshToken | None:
        token = await self.update_one(
            {"token_hash": token_hash},
            {
                "revoked": True,
                "updated_at": utc_now(),
            },
        )

        if token is None:
            return None

        return RefreshToken.model_validate(token)

    async def revoke_all_user_tokens(
        self,
        user_id: str,
    ) -> int:
        result = await self.update_many(
            {"user_id": user_id},
            {
                "revoked": True,
                "updated_at": utc_now(),
            },
        )

        return result.modified_count

    async def delete_expired_tokens(self) -> int:
        result = await self.collection.delete_many(
            {
                "expires_at": {
                    "$lt": utc_now()
                }
            }
        )

        return result.deleted_count

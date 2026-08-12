from app.common.constants import CollectionName
from app.repositories.base_repository import BaseRepository
from app.common.utils.datetime import utc_now


class ChatSessionDocumentRepository(
    BaseRepository,
):

    def __init__(self, db):

        super().__init__(
            db[
                CollectionName.CHAT_SESSION_DOCUMENTS.value
            ]
        )

    async def add_documents(
        self,
        session_id: str,
        document_ids: list[str],
    ):

      documents = []

      for document_id in document_ids:

          documents.append(
              {
                  "session_id": session_id,
                  "document_id": document_id,
                  "created_at": utc_now(),
              }
          )

      await self.collection.insert_many(
          documents,
      )

    async def get_document_ids(
        self,
        session_id: str,
    ) -> list[str]:

        cursor = self.collection.find(
            {
                "session_id": session_id,
            }
        )

        documents = await cursor.to_list(
            length=None,
        )

        return [
            document["document_id"]
            for document in documents
        ]
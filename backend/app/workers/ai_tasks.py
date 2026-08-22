import asyncio
import logging
from datetime import UTC, datetime
from app.core.celery import celery_app
from app.workers.database import get_worker_database
from app.workers.base import run_async_task
from app.modules.search.service import SearchService
from app.modules.chat.service import ChatService
from app.common.constants import ChatRole
from app.services.ai.service import AIService
from app.common.utils.datetime import utc_now

logger = logging.getLogger(__name__)

PROACTIVE_INSIGHTS_PROMPT = """You are a proactive AI Document Intelligence Analyst.

Here is a consolidated table of data extracted from a batch of newly uploaded documents:
{table}

Generate a helpful, conversational proactive analysis greeting message.
Rules:
1. Address the user directly in a friendly, professional tone (e.g., "I've finished analyzing your newly uploaded documents...").
2. Identify and highlight 2-3 key insights, observations, or anomalies (e.g., a specific invoice has a total that is much higher or lower than the others, a supplier has different bank details in one invoice vs another, or specific key dates/products). Be extremely specific and numeric.
3. Keep it brief (max 3-4 bullet points).
4. Suggest a follow-up action to help the user query this data further (e.g., "Would you like me to compare specific line items?").
5. Do NOT output a raw Markdown table yourself; refer to the data extracted from the documents.
6. If the fields in the table are mostly N/A (indicating these are not invoices), write a concise proactive greeting summarizing what these documents appear to be based on their filenames and any available text snippets.

Proactive Analysis:"""

@celery_app.task(
    name="ai.generate_proactive_insights",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    retry_kwargs={
        "max_retries": 3,
    },
)
def generate_proactive_insights_task(
    owner_id: str,
    document_ids: list[str],
):
    run_async_task(
        run_proactive_insights(
            owner_id=owner_id,
            document_ids=document_ids,
        )
    )

async def run_proactive_insights(
    owner_id: str,
    document_ids: list[str],
):
    logger.info("Starting proactive insights analysis for user %s and documents %s", owner_id, document_ids)
    
    client, db = await get_worker_database()
    
    search_service = SearchService(db)
    chat_service = ChatService(db)
    ai_service = AIService()
    
    # 1. Run the structured batch extraction pipeline to get the table
    try:
        md_table, content_sources, metadata_sources = await search_service._run_extraction_pipeline(
            document_ids=document_ids,
            question="Compare newly uploaded documents",
            owner_id=owner_id
        )
        sources = content_sources + metadata_sources
    except Exception as e:
        logger.error("Failed to run extraction pipeline for proactive insights: %s", e)
        return
        
    if not md_table:
        logger.warning("No extraction table was generated, skipping proactive insights.")
        return
        
    # 2. Run LLM call to get insights
    prompt = PROACTIVE_INSIGHTS_PROMPT.format(table=md_table)
    try:
        response = await ai_service.answer_question(prompt=prompt)
        insight_content = response.get("answer", "")
    except Exception as e:
        logger.error("Failed to generate proactive insights from LLM: %s", e)
        return
        
    if not insight_content:
        logger.warning("LLM returned empty insights, skipping.")
        return
        
    # 3. Create a new chat session linked to these documents
    try:
        session = await chat_service.create_session(
            owner_id=owner_id,
            document_ids=document_ids
        )
        session_id = str(session.id)
        
        # 4. Insert proactive greeting assistant message
        await chat_service.repository.create_message({
            "session_id": session_id,
            "role": ChatRole.ASSISTANT,
            "content": insight_content,
            "sources": sources,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC)
        })
        
        # 5. Generate and update a smart title for the chat session
        doc_meta = await search_service._get_document_metadata(document_ids)
        doc_names = [doc["document_name"] for doc in doc_meta if doc.get("document_name")]
        
        if len(doc_names) == 1:
            title = f"Proactive Analysis: {doc_names[0]}"
        elif len(doc_names) > 1:
            title = f"Proactive Analysis: {doc_names[0]} & {len(doc_names)-1} others"
        else:
            title = "Proactive Analysis"
            
        await chat_service.repository.update(
            session_id,
            {
                "title": title,
                "title_generated": True,
                "updated_at": utc_now(),
            }
        )
        
        logger.info("Successfully generated proactive insights in chat session %s", session_id)
        
    except Exception as e:
        logger.error("Failed to complete proactive insights session setup: %s", e)

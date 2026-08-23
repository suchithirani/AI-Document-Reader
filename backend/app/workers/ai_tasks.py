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


MEMORY_EXTRACTION_PROMPT = """You are an AI Memory Assistant. Analyze the following conversation between the User and the Assistant:
{conversation}

Identify any core user preferences, recurring inquiries, business constants, document verification rules, or important facts about the user's files/workflows that should be remembered across sessions.
Examples:
- "User is verifying invoices from Sheth Matarmal Khanchand"
- "User prefers all currency amounts to be written out in word form"
- "User wants tax components CGST and SGST summed up automatically"

Do NOT extract transient chit-chat, session-specific file names (unless relevant to recurring queries), or casual remarks.
Return a list of 1-3 concise memory statements, each as a single sentence. If nothing important is found, return an empty JSON list.

Response (strictly a valid JSON list of strings only):"""

MEMORY_CONSOLIDATION_PROMPT = """You are an AI Memory Consolidator. 

Here is the user's existing list of long-term memories/preferences:
{existing_memories}

Here are the new observations from the latest conversation:
{new_observations}

Merge them into a single consolidated list of up to 10 unique, clean memory statements.
Rules:
1. Remove duplicate or redundant rules.
2. Resolve any direct contradictions (preferring the newer observation).
3. Keep each statement as a single, clear sentence.
4. Format the final output strictly as a JSON list of strings.

Response (strictly a valid JSON list of strings only):"""

@celery_app.task(
    name="ai.update_user_memory",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    retry_kwargs={
        "max_retries": 3,
    },
)
def update_user_memory_task(
    owner_id: str,
    session_id: str,
):
    run_async_task(
        run_update_user_memory(
            owner_id=owner_id,
            session_id=session_id,
        )
    )

async def run_update_user_memory(
    owner_id: str,
    session_id: str,
):
    logger.info("Updating user memory profile for user %s based on session %s", owner_id, session_id)
    client, db = await get_worker_database()
    chat_service = ChatService(db)
    ai_service = AIService()

    # 1. Fetch all messages in the session
    try:
        messages = await chat_service.repository.get_messages(session_id)
    except Exception as e:
        logger.error("Failed to retrieve messages for memory update: %s", e)
        return

    if not messages:
        logger.warning("No messages found in session %s, skipping memory extraction.", session_id)
        return

    # Format conversation history
    convo_parts = []
    for msg in messages:
        role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
        content = msg.content if hasattr(msg, 'content') else msg.get("content", "")
        convo_parts.append(f"{role.upper()}: {content}")
    conversation_text = "\n\n".join(convo_parts)

    # 2. Extract new observations
    extract_prompt = MEMORY_EXTRACTION_PROMPT.format(conversation=conversation_text)
    try:
        response = await ai_service.answer_question(prompt=extract_prompt)
        raw_observations = response.get("answer", "")
    except Exception as e:
        logger.error("Failed to run memory extraction prompt: %s", e)
        return

    import json, re
    new_obs = []
    cleaned_obs_json = raw_observations.strip()
    if cleaned_obs_json.startswith("```"):
        cleaned_obs_json = re.sub(r"^```(?:json)?", "", cleaned_obs_json).strip()
        cleaned_obs_json = re.sub(r"```$", "", cleaned_obs_json).strip()

    try:
        new_obs = json.loads(cleaned_obs_json)
    except Exception:
        # Fallback regex array search
        match = re.search(r"\[\s*\".*\"\s*\]", raw_observations, re.DOTALL)
        if match:
            try:
                new_obs = json.loads(match.group(0))
            except Exception:
                pass

    if not new_obs or not isinstance(new_obs, list):
        logger.info("No new memories or preferences detected in conversation, skipping consolidation.")
        return

    # 3. Load existing memories
    from app.common.constants import CollectionName
    memories_col = db[CollectionName.USER_MEMORIES.value]
    existing_doc = await memories_col.find_one({"owner_id": owner_id})
    existing_memories = existing_doc.get("memories", []) if existing_doc else []

    # 4. Consolidate memories via LLM
    consolidation_prompt = MEMORY_CONSOLIDATION_PROMPT.format(
        existing_memories=json.dumps(existing_memories),
        new_observations=json.dumps(new_obs)
    )
    try:
        response = await ai_service.answer_question(prompt=consolidation_prompt)
        raw_consolidated = response.get("answer", "")
    except Exception as e:
        logger.error("Failed to run memory consolidation prompt: %s", e)
        return

    cleaned_con_json = raw_consolidated.strip()
    if cleaned_con_json.startswith("```"):
        cleaned_con_json = re.sub(r"^```(?:json)?", "", cleaned_con_json).strip()
        cleaned_con_json = re.sub(r"```$", "", cleaned_con_json).strip()

    consolidated_list = []
    try:
        consolidated_list = json.loads(cleaned_con_json)
    except Exception:
        match = re.search(r"\[\s*\".*\"\s*\]", raw_consolidated, re.DOTALL)
        if match:
            try:
                consolidated_list = json.loads(match.group(0))
            except Exception:
                pass

    if not isinstance(consolidated_list, list):
        logger.error("Consolidated memories response was not a valid list: %s", raw_consolidated)
        return

    # 5. Save back to MongoDB
    try:
        await memories_col.update_one(
            {"owner_id": owner_id},
            {
                "$set": {
                    "memories": consolidated_list[:10],
                    "updated_at": datetime.now(UTC)
                }
            },
            upsert=True
        )
        logger.info("Successfully updated memory profile for user %s. Active memories: %d", owner_id, len(consolidated_list))
    except Exception as e:
        logger.error("Failed to save consolidated memories to MongoDB: %s", e)


METADATA_EXTRACTION_PROMPT = """You are an AI Document Analyzer. Analyze the following document text segment:
{text}

Extract the following metadata:
1. document_type: Classify into one of: "invoice", "receipt", "agreement", "resume", "report", "unknown".
2. description: A single-sentence summary of what this document is (e.g. "Invoice SMK/436/26-27 from Sheth Matarmal Khanchand for ₹10,080.00 dated 15/08/2026").
3. tags: A list of 2-4 keywords or tags relevant to this document.
4. extracted_metadata: A JSON object containing key-value pairs of any critical fields found (e.g., supplier, date, total, candidate_name, contract_parties, etc.).

Format your response strictly as a JSON object with these keys: "document_type", "description", "tags", "extracted_metadata".

Response (strictly valid JSON only):"""

@celery_app.task(
    name="ai.extract_document_metadata",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    retry_kwargs={
        "max_retries": 3,
    },
)
def extract_document_metadata_task(
    owner_id: str,
    document_id: str,
):
    run_async_task(
        run_extract_document_metadata(
            owner_id=owner_id,
            document_id=document_id,
        )
    )

async def run_extract_document_metadata(
    owner_id: str,
    document_id: str,
):
    logger.info("Extracting metadata for document %s", document_id)
    client, db = await get_worker_database()
    ai_service = AIService()

    # 1. Fetch first few chunks of the document
    from app.common.constants import CollectionName
    chunks_col = db[CollectionName.DOCUMENT_CHUNKS.value]
    chunks = await chunks_col.find({"document_id": document_id}).sort("index", 1).limit(4).to_list(4)
    
    if not chunks:
        logger.warning("No chunks found for document %s, skipping metadata extraction.", document_id)
        return
        
    texts = []
    for c in chunks:
        text = c.get("content") or c.get("text") or ""
        texts.append(text)
    document_text = "\n\n".join(texts)[:6000]

    # 2. Call LLM to extract metadata
    prompt = METADATA_EXTRACTION_PROMPT.format(text=document_text)
    try:
        response = await ai_service.answer_question(prompt=prompt)
        raw_meta = response.get("answer", "")
    except Exception as e:
        logger.error("Failed to call LLM for document metadata extraction: %s", e)
        return

    import json, re
    cleaned_json = raw_meta.strip()
    if cleaned_json.startswith("```"):
        cleaned_json = re.sub(r"^```(?:json)?", "", cleaned_json).strip()
        cleaned_json = re.sub(r"```$", "", cleaned_json).strip()

    meta_dict = {}
    try:
        meta_dict = json.loads(cleaned_json)
    except Exception:
        match = re.search(r"\{\s*\".*\"\s*\}", raw_meta, re.DOTALL)
        if match:
            try:
                meta_dict = json.loads(match.group(0))
            except Exception:
                pass

    if not meta_dict or not isinstance(meta_dict, dict):
        logger.error("Failed to parse extracted metadata response: %s", raw_meta)
        return

    description = meta_dict.get("description", "Unknown document")
    doc_type = meta_dict.get("document_type", "unknown")
    tags = meta_dict.get("tags", [])
    extracted_metadata = meta_dict.get("extracted_metadata", {})

    # 3. Save to documents collection
    docs_col = db[CollectionName.DOCUMENTS.value]
    from bson import ObjectId
    try:
        await docs_col.update_one(
            {"_id": ObjectId(document_id)},
            {
                "$set": {
                    "description": description,
                    "document_type": doc_type,
                    "tags": tags,
                    "extracted_metadata": extracted_metadata,
                    "updated_at": datetime.now(UTC)
                }
            }
        )
        logger.info("Successfully extracted and saved metadata for document %s (type: %s)", document_id, doc_type)
        
        # Evict Redis cache for owner to ensure UI displays metadata instantly
        doc = await docs_col.find_one({"_id": ObjectId(document_id)})
        if doc and doc.get("owner_id"):
            owner_id = doc.get("owner_id")
            from app.services.cache.response import ResponseCache
            cache = ResponseCache()
            await cache.delete(f"documents:{owner_id}:0:20")
            logger.info("Evicted documents list cache for owner %s after metadata extraction", owner_id)
    except Exception as e:
        logger.error("Failed to save extracted metadata to MongoDB: %s", e)



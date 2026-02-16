"""
OpenAI Responses API → Chat Completions API Proxy

This proxy translates between Open WebUI's expected Chat Completions API
and OpenAI's newer Responses API, enabling access to latest models.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import os
import json
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OpenAI Responses API Proxy")

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# Model mapping: Chat Completions name → Responses API name
MODEL_MAPPING = {
    "chatgpt-4o-latest": "chatgpt-4o-latest",
    "gpt-4.1": "gpt-4.1",
    "gpt-5.2-chat-latest": "gpt-5.2-chat-latest",
    # Fallback: if not in mapping, use as-is
}


def map_model_name(model: str) -> str:
    """Map Chat Completions model name to Responses API name."""
    return MODEL_MAPPING.get(model, model)


def convert_chat_to_responses_format(chat_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Chat Completions request to Responses API format.

    Chat Completions format:
    {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7,
        ...
    }

    Responses API format (simplified, adjust as needed):
    {
        "model": "chatgpt-4o-latest",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7,
        ...
    }

    Note: Actual Responses API format may differ - adjust based on OpenAI docs.
    """
    responses_request = chat_request.copy()

    # Map model name
    if "model" in responses_request:
        responses_request["model"] = map_model_name(responses_request["model"])

    return responses_request


def convert_responses_to_chat_format(responses_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Responses API response to Chat Completions format.

    This ensures Open WebUI can parse the response correctly.
    """
    # If response is already in Chat Completions format, return as-is
    if "choices" in responses_response:
        return responses_response

    # Otherwise, transform (adjust based on actual Responses API format)
    # This is a placeholder - adjust based on real Responses API structure
    return responses_response


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "OpenAI Responses API Proxy",
        "openai_configured": bool(OPENAI_API_KEY)
    }


@app.get("/health")
async def health():
    """Health check for Docker."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    return {"status": "healthy"}


@app.get("/v1/models")
async def list_models():
    """
    List available models.
    Open WebUI calls this to populate the model dropdown.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=401, detail="OPENAI_API_KEY not set")

    # Fetch models from OpenAI
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{OPENAI_BASE_URL}/models",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
            )
            response.raise_for_status()
            models_data = response.json()

            # Add custom models that may not be in the standard list
            custom_models = [
                {
                    "id": "chatgpt-4o-latest",
                    "object": "model",
                    "created": 1700000000,
                    "owned_by": "openai"
                },
                {
                    "id": "gpt-4.1",
                    "object": "model",
                    "created": 1700000000,
                    "owned_by": "openai"
                },
            ]

            # Merge with official list
            if "data" in models_data:
                models_data["data"].extend(custom_models)

            return models_data

    except httpx.HTTPError as e:
        logger.error(f"Error fetching models: {e}")
        raise HTTPException(status_code=502, detail=f"Error fetching models from OpenAI: {str(e)}")


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    Chat Completions endpoint that proxies to OpenAI.

    For newer models, translates to Responses API if needed.
    For older models, passes through to standard Chat Completions API.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=401, detail="OPENAI_API_KEY not set")

    try:
        # Parse request body
        body = await request.json()
        model = body.get("model", "")
        is_streaming = body.get("stream", False)

        logger.info(f"Chat completion request for model: {model}, streaming: {is_streaming}")

        # Determine if we need to use Responses API
        use_responses_api = model in MODEL_MAPPING

        if use_responses_api:
            logger.info(f"Using Responses API for model: {model}")
            # Convert to Responses API format
            responses_body = convert_chat_to_responses_format(body)
            endpoint = f"{OPENAI_BASE_URL}/chat/completions"  # Adjust if Responses API uses different endpoint
        else:
            logger.info(f"Using standard Chat Completions API for model: {model}")
            responses_body = body
            endpoint = f"{OPENAI_BASE_URL}/chat/completions"

        # Forward request to OpenAI
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            if is_streaming:
                # Handle streaming response
                async def stream_generator():
                    async with httpx.AsyncClient(timeout=None) as client:
                        async with client.stream(
                            "POST",
                            endpoint,
                            headers=headers,
                            json=responses_body
                        ) as response:
                            response.raise_for_status()
                            async for chunk in response.aiter_bytes():
                                if chunk:
                                    yield chunk

                return StreamingResponse(
                    stream_generator(),
                    media_type="text/event-stream"
                )
            else:
                # Handle non-streaming response
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        endpoint,
                        headers=headers,
                        json=responses_body
                    )
                response.raise_for_status()

                result = response.json()

                # Convert response if needed
                if use_responses_api:
                    result = convert_responses_to_chat_format(result)

                return JSONResponse(content=result)

    except httpx.HTTPStatusError as e:
        logger.error(f"OpenAI API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"OpenAI API error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

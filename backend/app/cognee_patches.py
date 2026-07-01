import asyncio
import logging
from typing import Any
from pydantic import BaseModel
import litellm
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_not_exception_type,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)

def apply_patches():
    """
    Applies monkey-patches to cognee's mistral adapter and tokenizer
    to fix structured output schema parsing and prefix stripping.
    """
    try:
        from cognee.infrastructure.llm.structured_output_framework.litellm_instructor.llm.mistral.adapter import MistralAdapter
        from cognee.infrastructure.llm.tokenizer.Mistral.adapter import MistralTokenizer
        from mistral_common.tokens.tokenizers.mistral import MistralTokenizer as MistralCommonTokenizer
        from cognee.infrastructure.llm.retry_config import llm_retry_stop_condition
        from cognee.modules.observability.get_observe import get_observe
        from cognee.shared.rate_limiting import llm_rate_limiter_context_manager
    except ImportError as e:
        logger.warning(f"Could not import cognee modules for patching: {e}")
        return

    observe = get_observe()

    # 1. Patch MistralAdapter.acreate_structured_output
    @observe(as_type="generation")
    @retry(
        stop=llm_retry_stop_condition,
        wait=wait_exponential_jitter(8, 128),
        retry=retry_if_not_exception_type(
            (
                litellm.exceptions.NotFoundError,
                litellm.exceptions.AuthenticationError,
                asyncio.CancelledError,
            )
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def patched_acreate_structured_output(
        self, text_input: str, system_prompt: str, response_model: type[BaseModel], **kwargs
    ) -> BaseModel:
        try:
            messages = [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": f"Use the given format to extract information\n                from the following input: {text_input}",
                },
            ]
            merged_kwargs = {**self.llm_args, **kwargs}
            try:
                async with llm_rate_limiter_context_manager():
                    response = await self.aclient.chat.completions.create(
                        model=self.model,
                        max_retries=2,
                        messages=messages,
                        response_model=response_model,
                        **merged_kwargs,
                    )
                
                if isinstance(response, response_model):
                    return response
                if isinstance(response, BaseModel):
                    return response_model.model_validate(response.model_dump())
                
                if (
                    hasattr(response, "choices")
                    and response.choices
                    and response.choices[0].message is not None
                    and response.choices[0].message.content
                ):
                    content = response.choices[0].message.content
                    return response_model.model_validate_json(content)
                else:
                    raise ValueError("Failed to get valid response after retries")
            except litellm.exceptions.BadRequestError as e:
                logger.error(f"Bad request error: {str(e)}")
                raise ValueError(f"Invalid request: {str(e)}")

        except litellm.exceptions.JSONSchemaValidationError as e:
            logger.error(f"Schema validation failed: {str(e)}")
            logger.debug(f"Raw response: {getattr(e, 'raw_response', None)}")
            raise ValueError(f"Response failed schema validation: {str(e)}")

    MistralAdapter.acreate_structured_output = patched_acreate_structured_output

    # 2. Patch MistralTokenizer.__init__ to strip prefix
    def patched_tokenizer_init(self, model: str, max_completion_tokens: int = 3072):
        self.model = model
        self.max_completion_tokens = max_completion_tokens

        # Strip provider prefix e.g. "mistral/mistral-medium-latest" -> "mistral-medium-latest"
        bare_model = model.split("/")[-1] if "/" in model else model

        try:
            self.tokenizer = MistralCommonTokenizer.from_model(bare_model)
        except Exception:
            try:
                self.tokenizer = MistralCommonTokenizer.from_model("mistral-tiny-2312")
            except Exception:
                self.tokenizer = None
    
    def patched_extract_tokens(self, text: str) -> list[Any]:
        if getattr(self, "tokenizer", None) is None:
            return list(text)
        from mistral_common.protocol.instruct.messages import UserMessage, Roles
        from mistral_common.protocol.instruct.request import ChatCompletionRequest

        encoding = self.tokenizer.encode_chat_completion(
            ChatCompletionRequest(
                messages=[UserMessage(role=Roles.user, content=text)],
                model=self.model,
            )
        )
        return encoding.tokens

    def patched_count_tokens(self, text: str) -> int:
        if getattr(self, "tokenizer", None) is None:
            return max(1, len(text) // 4)
        return len(self.extract_tokens(text))

    MistralTokenizer.__init__ = patched_tokenizer_init
    MistralTokenizer.extract_tokens = patched_extract_tokens
    MistralTokenizer.count_tokens = patched_count_tokens
    
    logger.info("Successfully applied cognee monkey-patches for Mistral adapter and tokenizer.")

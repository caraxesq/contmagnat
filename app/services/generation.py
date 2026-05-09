from dataclasses import dataclass
from typing import Protocol

from app.services.prompt_builder import build_generation_prompt
from app.services.text_generation import MockTextGenerator, TextGenerator
from app.core.errors import GenerationNotConfiguredError

import logging

logger = logging.getLogger(__name__)


class GenerationLogsRepositoryProtocol(Protocol):
    async def add_log(
        self,
        *,
        topic: str,
        user_request: str,
        generated_text: str | None,
        status: str,
        custom_topic: str | None = None,
        prompt: str | None = None,
        **kwargs: object,
    ) -> object:
        pass


@dataclass(frozen=True)
class GenerationResult:
    status: str
    generated_text: str


def _is_list_paragraph(text: str) -> bool:
    """Check if paragraph is a list or list header."""
    lines = text.strip().split("\n")
    list_markers = ("–", "-", "•", "▸", "►")
    # It's a list if any line starts with a list marker
    for line in lines:
        stripped = line.strip()
        if any(stripped.startswith(m) for m in list_markers):
            return True
    # It's a list header if it ends with ":"
    if lines[0].strip().endswith(":"):
        return True
    return False


def _already_formatted(text: str) -> bool:
    """Check if text already has ** or * formatting."""
    return "**" in text or (text.count("*") >= 2 and "**" not in text)


def _post_process(text: str) -> str:
    """Fix formatting issues that LLMs stubbornly produce despite prompt bans.

    Replaces:
    - ▸ and ► with – (en dash) in list items
    - • with – (en dash) in list items
    - — (em dash) at the start of lines with – (en dash) for list items
    """
    import re as _re

    lines = text.split("\n")
    result = []
    for line in lines:
        stripped = line.lstrip()
        # Replace ▸, ►, • at line start with –
        if stripped.startswith("▸") or stripped.startswith("►") or stripped.startswith("•"):
            leading = line[: len(line) - len(stripped)]
            line = leading + "–" + stripped[1:]
        # Replace — at line start (em dash used as list marker) with –
        elif stripped.startswith("— ") or stripped == "—":
            leading = line[: len(line) - len(stripped)]
            line = leading + "–" + stripped[1:]
        result.append(line)
    return "\n".join(result)


def _apply_formatting(text: str) -> str:
    """Apply bold (**) and italic (*) formatting programmatically.

    LLMs typically don't output literal asterisk characters in their
    response text, so this function adds formatting based on the post
    structure:
    - Bold: the final "punch" paragraph (last non-list, non-CTA paragraph)
    - Bold: a key factual paragraph in the body (medium-length, contains
      numbers or strong claims)
    - Italic: a short standalone observation or story moment
    """
    # First, fix forbidden characters
    text = _post_process(text)

    if _already_formatted(text):
        return text

    paragraphs = text.split("\n\n")
    if len(paragraphs) < 3:
        return text

    formatted = list(paragraphs)
    bold_indices: list[int] = []
    italic_index: int | None = None

    # --- BOLD: last meaningful paragraph (the "punch") ---
    for i in range(len(formatted) - 1, -1, -1):
        p = formatted[i].strip()
        if not p:
            continue
        if _is_list_paragraph(p):
            continue
        bold_indices.append(i)
        break

    # --- BOLD: find a key factual paragraph in the body ---
    # Look for a paragraph that contains numbers, specific facts,
    # or strong language — skip first (hook) and last (already bold)
    skip = set(bold_indices)
    skip.add(0)  # skip the hook
    for i in range(1, len(formatted) - 1):
        if i in skip:
            continue
        p = formatted[i].strip()
        if not p or _is_list_paragraph(p) or len(p) < 40:
            continue
        # Prefer paragraphs with numbers, percentages, specific data
        has_data = any(ch.isdigit() for ch in p)
        has_strong = any(
            marker in p.lower()
            for marker in ("процент", "каждый", "миллион", "тысяч", "%", "раз в")
        )
        if has_data or has_strong:
            bold_indices.append(i)
            break

    # --- ITALIC: short standalone observation/story moment ---
    skip_for_italic = set(bold_indices)
    skip_for_italic.add(0)
    for i in range(1, len(formatted)):
        if i in skip_for_italic:
            continue
        p = formatted[i].strip()
        if not p or _is_list_paragraph(p):
            continue
        # Short paragraph, single sentence or two — a story moment
        if 20 < len(p) < 180 and "\n" not in p:
            italic_index = i
            break

    # --- Apply formatting ---
    for idx in bold_indices:
        p = formatted[idx].strip()
        if p and not p.startswith("**"):
            formatted[idx] = f"**{p}**"

    if italic_index is not None:
        p = formatted[italic_index].strip()
        if p and not p.startswith("*"):
            formatted[italic_index] = f"*{p}*"

    return "\n\n".join(formatted)


class GenerationService:
    def __init__(
        self,
        *,
        generation_logs_repository: GenerationLogsRepositoryProtocol | None = None,
        text_generator: TextGenerator | None = None,
    ) -> None:
        self.generation_logs_repository = generation_logs_repository
        self.text_generator = text_generator or MockTextGenerator()

    async def generate_post(
        self,
        *,
        topic: str,
        user_request: str,
        custom_topic: str | None = None,
        style_examples: list[str] | None = None,
    ) -> GenerationResult:
        prompt_topic = f"{topic}: {custom_topic}" if custom_topic else topic
        prompt = build_generation_prompt(
            topic=prompt_topic,
            user_request=user_request,
            style_examples=style_examples or [],
        )
        logger.info("Generation request received", extra={"topic": topic, "custom_topic": custom_topic})

        try:
            generated_text = await self.text_generator.generate(prompt)
            logger.info("Model raw response: %s", generated_text)
            # LLMs don't output literal * characters, so apply formatting in code
            generated_text = _apply_formatting(generated_text)
            logger.info("After formatting: %s", generated_text)
            status = "ok"
        except GenerationNotConfiguredError as error:
            logger.warning("Generation provider is not configured: %s", error)
            generated_text = f"Ошибка генерации: {error}"
            status = "error"
        except Exception:
            logger.exception("Generation failed")
            generated_text = "Ошибка генерации. Подробности записаны в лог."
            status = "error"

        if self.generation_logs_repository is not None:
            await self.generation_logs_repository.add_log(
                topic=topic,
                custom_topic=custom_topic,
                user_request=user_request,
                generated_text=generated_text,
                status=status,
                prompt=prompt,
            )

        return GenerationResult(status=status, generated_text=generated_text)

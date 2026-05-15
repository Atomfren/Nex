"""Локальный AI ассистент на llama-cpp-python."""

import os
from pathlib import Path
from typing import Optional, AsyncGenerator

from loguru import logger

from backend.config import settings

try:
    from llama_cpp import Llama
    _LLAMA_AVAILABLE = True
except ImportError:
    _LLAMA_AVAILABLE = False
    Llama = None


class LocalAssistant:
    """Локальный LLM ассистент."""

    _instance: Optional["LocalAssistant"] = None
    _model: Optional[Llama] = None

    SYSTEM_PROMPT = (
        "You are NexoraLauncher AI Assistant. Help users with Minecraft launcher questions. "
        "Answer in the same language as the user. Be concise and helpful.\n"
    )

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load_model(self):
        """Ленивая загрузка модели."""
        if self._model is not None:
            return self._model

        if not _LLAMA_AVAILABLE:
            raise RuntimeError(
                "llama-cpp-python не установлен. "
                "Установите: pip install llama-cpp-python"
            )

        model_path = settings.ai_model_path
        if not model_path or not Path(model_path).exists():
            data_dir = Path(__file__).parent.parent.parent / "data"
            gguf_files = list(data_dir.glob("*.gguf"))
            if gguf_files:
                model_path = str(gguf_files[0])
            else:
                raise FileNotFoundError(
                    "AI model not found. Set QUANTUMLAUNCHER_BACKEND_AI_MODEL_PATH "
                    "or place a .gguf file in the data directory."
                )

        logger.info(f"Loading LLM model from {model_path}")
        self._model = Llama(
            model_path=model_path,
            n_ctx=settings.ai_n_ctx,
            n_threads=settings.ai_n_threads,
            verbose=False,
        )
        logger.info("LLM model loaded")
        return self._model

    def ask(self, message: str) -> str:
        """Синхронный запрос к AI."""
        model = self._load_model()
        prompt = f"{self.SYSTEM_PROMPT}User: {message}\nAssistant:"
        output = model(
            prompt,
            max_tokens=512,
            stop=["User:", "\nUser:"],
            temperature=0.7,
        )
        text = output["choices"][0]["text"].strip()
        return text

    def ask_stream(self, message: str) -> AsyncGenerator[str, None]:
        """Стриминговый запрос к AI (генератор токенов)."""
        model = self._load_model()
        prompt = f"{self.SYSTEM_PROMPT}User: {message}\nAssistant:"
        stream = model(
            prompt,
            max_tokens=512,
            stop=["User:", "\nUser:"],
            temperature=0.7,
            stream=True,
        )
        for chunk in stream:
            token = chunk["choices"][0]["text"]
            yield token

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def is_available(self) -> bool:
        """Проверяет, доступна ли модель."""
        if not _LLAMA_AVAILABLE:
            return False
        model_path = settings.ai_model_path
        if model_path and Path(model_path).exists():
            return True
        data_dir = Path(__file__).parent.parent.parent / "data"
        return bool(list(data_dir.glob("*.gguf")))

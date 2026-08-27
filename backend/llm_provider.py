"""Multi-Provider Generative LLM Client (Gemini, OpenAI, Groq, Local Ollama)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger("llm_provider")

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"


def load_env_file() -> None:
    """Lightweight .env loader that does not require python-dotenv."""
    if not ENV_FILE.exists():
        return
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and v:
                    os.environ[k] = v
    except Exception as e:
        logger.warning(f"Failed to read .env file: {e}")


class LLMProvider:
    """Unified LLM Provider supporting Google Gemini, OpenAI, Groq, and Ollama."""

    def __init__(self) -> None:
        load_env_file()

    def get_active_provider_info(self) -> Dict[str, Any]:
        """Returns the currently active provider name and model."""
        load_env_file()
        gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")
        groq_key = os.environ.get("GROQ_API_KEY")
        ollama_url = os.environ.get("OLLAMA_BASE_URL")

        if gemini_key:
            return {"provider": "gemini", "model": "gemini-1.5-flash", "has_key": True}
        if openai_key:
            return {"provider": "openai", "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), "has_key": True}
        if groq_key:
            return {"provider": "groq", "model": "llama-3.3-70b-versatile", "has_key": True}
        if ollama_url:
            return {"provider": "ollama", "model": os.environ.get("OLLAMA_MODEL", "qwen2.5:7b"), "has_key": True}

        return {"provider": "offline_deterministic", "model": "rule_rag_engine", "has_key": False}

    def is_llm_available(self) -> bool:
        return self.get_active_provider_info()["has_key"]

    def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.3) -> Optional[str]:
        """Generates a text completion from the active LLM provider."""
        provider_info = self.get_active_provider_info()
        provider = provider_info["provider"]

        if provider == "gemini":
            return self._call_gemini(prompt, system_prompt, temperature)
        elif provider == "openai":
            return self._call_openai(prompt, system_prompt, temperature)
        elif provider == "groq":
            return self._call_groq(prompt, system_prompt, temperature)
        elif provider == "ollama":
            return self._call_ollama(prompt, system_prompt, temperature)

        return None

    def _call_gemini(self, prompt: str, system_prompt: str, temperature: float) -> Optional[str]:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"[SYSTEM INSTRUCTION]\n{system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Dimengerti. Saya siap bertindak sebagai AI Business Copilot profesional untuk Nashta."}]})
        
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            }
        }

        try:
            resp = requests.post(url, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            else:
                logger.error(f"Gemini API error ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.error(f"Gemini call failed: {e}")
        return None

    def _call_openai(self, prompt: str, system_prompt: str, temperature: float) -> Optional[str]:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None

        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
            else:
                logger.error(f"OpenAI API error ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
        return None

    def _call_groq(self, prompt: str, system_prompt: str, temperature: float) -> Optional[str]:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return None

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
            else:
                logger.error(f"Groq API error ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.error(f"Groq call failed: {e}")
        return None

    def _call_ollama(self, prompt: str, system_prompt: str, temperature: float) -> Optional[str]:
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
        url = f"{base_url}/api/generate"

        payload = {
            "model": model,
            "system": system_prompt,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }

        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                return resp.json().get("response", "")
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
        return None


llm_provider = LLMProvider()

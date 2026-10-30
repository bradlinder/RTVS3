"""
scripts/local_proxy.py - Autonomous Local AI Smart Routing Proxy
Milestone 2.8: Autonomous Model Routing & Natural Language Dispatcher

Provides a zero-external-dependency, OpenAI-compatible HTTP proxy (http://127.0.0.1:8000/v1)
that connects VS Code (Continue, Cline, Antigravity) to local Ollama models.
Inspects natural language prompt queries and context scopes in <5ms, dynamically
dispatching each request to the optimal model (Qwen 3.8 27B, Qwen 3 14B, Qwen 2.5 Coder 32B,
or DeepSeek-R1 14B) without requiring manual model selection or memorized commands.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple

# Import task router for AST-aware routing logic
try:
    from scripts.task_router import TaskRouter, RouteRecommendation
except ImportError:
    from task_router import TaskRouter, RouteRecommendation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [ROUTER] %(message)s")
logger = logging.getLogger("SmartRouter")

OLLAMA_DEFAULT_URL = "http://127.0.0.1:11434"
PROXY_DEFAULT_PORT = 8000

# Mapping from TaskRouter canonical models to Ollama tags
MODEL_MAP = {
    "qwen3.8-27b": "qwen3.8-27b",
    "qwen3.8-27b-q3": "qwen3.8-27b",
    "qwen3:14b": "qwen3:14b",
    "qwen3.5:9b": "qwen3.5:9b",
    "qwen2.5-coder:32b": "qwen2.5-coder:32b",
    "qwen2.5-coder:32b-rtvs": "qwen2.5-coder:32b",
    "qwen2.5-coder:14b": "qwen2.5-coder:14b",
    "qwen2.5-coder:14b-rtvs": "qwen2.5-coder:14b",
    "qwen2.5-coder:7b": "qwen2.5-coder:7b",
    "qwen2.5-coder:7b-rtvs": "qwen2.5-coder:7b",
    "deepseek-r1:14b": "deepseek-r1:14b",
    "minicpm-v:latest": "minicpm-v:latest",
}


def classify_and_route(prompt: str, context_lines: int = 0) -> Tuple[str, str, str]:
    """
    Evaluates natural language prompt and context to select the best model.
    Returns: (target_ollama_model, category_name, rationale)
    """
    p_lower = prompt.lower()

    # 1. Surgical diff / minimal patch intent -> Qwen 2.5 Coder (no fluff, exact diff)
    diff_keywords = ["patch", "diff", "replace line", "surgical", "just the fix", "only the code", "regex"]
    if any(dk in p_lower for dk in diff_keywords) and not any(rk in p_lower for rk in TaskRouter.REFACTOR_KEYWORDS):
        return ("qwen2.5-coder:32b", "Surgical Diff & Precise Patch", "Targeted code fix requires zero conversational fluff.")

    # 2. Concurrency, deep reasoning & proof -> DeepSeek-R1
    if any(rk in p_lower for rk in TaskRouter.REASONING_KEYWORDS):
        return ("deepseek-r1:14b", "Deep Concurrency & Deductive Proof", "Step-by-step chain-of-thought analysis for complex concurrency/logic.")

    # 3. Vision / Screenshot inspection
    if any(vk in p_lower for vk in TaskRouter.VISION_KEYWORDS) and ("screenshot" in p_lower or "png" in p_lower or "image" in p_lower):
        return ("minicpm-v:latest", "Visual & Layout Inspection", "Multimodal visual encoder required for image/UI inspection.")

    # 4. Large-scale architecture, decomposition, or broad context -> Qwen 3.8 27B
    if any(rf in p_lower for rf in TaskRouter.REFACTOR_KEYWORDS) or context_lines >= 400:
        return ("qwen3.8-27b", "Architecture & Decomposition", "Multi-file reasoning, 262k context scaling, and agentic refactoring.")

    # 5. Fallback via full TaskRouter symbol analysis
    rec: RouteRecommendation = TaskRouter.route_task(prompt)
    target = MODEL_MAP.get(rec.recommended_model, "qwen3:14b")
    return (target, rec.category, rec.rationale)


class SmartRouterHandler(BaseHTTPRequestHandler):
    """Zero-dependency HTTP request handler implementing the OpenAI v1 chat endpoint."""

    ollama_url: str = OLLAMA_DEFAULT_URL

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        """Handle GET /v1/models endpoint."""
        self._send_cors_headers()
        if self.path in ("/v1/models", "/models"):
            models_payload = {
                "object": "list",
                "data": [
                    {"id": "rtvs-smart-router", "object": "model", "owned_by": "rtvs-local"},
                    {"id": "qwen3.8-27b", "object": "model", "owned_by": "alibaba"},
                    {"id": "qwen3:14b", "object": "model", "owned_by": "alibaba"},
                    {"id": "qwen2.5-coder:32b", "object": "model", "owned_by": "alibaba"},
                    {"id": "deepseek-r1:14b", "object": "model", "owned_by": "deepseek"},
                ],
            }
            body = json.dumps(models_payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path in ("/", "/health"):
            body = b'{"status": "ok", "service": "rtvs-smart-router"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        """Handle POST /v1/chat/completions endpoint."""
        self._send_cors_headers()
        if not (self.path.startswith("/v1/chat/completions") or self.path.startswith("/chat/completions")):
            self.send_response(404)
            self.end_headers()
            return

        content_len = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_len).decode("utf-8", errors="ignore")

        try:
            req_data = json.loads(raw_body)
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Invalid JSON payload: {e}"}).encode("utf-8"))
            return

        messages = req_data.get("messages", [])
        requested_model = req_data.get("model", "rtvs-smart-router")
        stream = req_data.get("stream", False)

        # Extract last user query
        user_query = ""
        context_len_chars = 0
        for m in reversed(messages):
            if m.get("role") == "user":
                content = m.get("content", "")
                if isinstance(content, str):
                    user_query = content
                elif isinstance(content, list):
                    # Multimodal content block
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            user_query += part.get("text", "") + " "
                break

        for m in messages:
            content = m.get("content", "")
            if isinstance(content, str):
                context_len_chars += len(content)

        context_lines = context_len_chars // 80

        # Autonomous Routing
        if requested_model in ("rtvs-smart-router", "default", "auto", ""):
            target_model, category, rationale = classify_and_route(user_query, context_lines)
            badge = f"<!-- [Routed to {target_model} | {category}] -->\n"
            logger.info("Natural Language Query: %r", (user_query[:60] + "...") if len(user_query) > 60 else user_query)
            logger.info("Routing decision: %s -> %s (%s)", requested_model, target_model, rationale)
        else:
            target_model = requested_model
            badge = ""
            logger.info("Explicit model passthrough: %s", target_model)

        # Forward to Ollama /api/chat
        ollama_payload = {
            "model": target_model,
            "messages": messages,
            "stream": stream,
        }
        if "options" in req_data:
            ollama_payload["options"] = req_data["options"]

        ollama_endpoint = f"{self.ollama_url}/api/chat"

        try:
            req = urllib.request.Request(
                ollama_endpoint,
                data=json.dumps(ollama_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=120)
        except urllib.error.URLError as e:
            logger.error("Failed to connect to Ollama at %s: %s", ollama_endpoint, e)
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            err_json = json.dumps({"error": f"Ollama connection error at {self.ollama_url}: {e}"}).encode("utf-8")
            self.wfile.write(err_json)
            return

        if stream:
            self._handle_streaming_response(resp, target_model, badge)
        else:
            self._handle_blocking_response(resp, target_model, badge)

    def _handle_streaming_response(self, resp: Any, target_model: str, badge: str) -> None:
        """Streams SSE chunks in standard OpenAI format to VS Code / Continue."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        req_id = f"chatcmpl-{int(time.time() * 1000)}"

        # Send optional badge as first token if present
        if badge:
            first_chunk = {
                "id": req_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": target_model,
                "choices": [{"index": 0, "delta": {"content": badge}, "finish_reason": None}],
            }
            self.wfile.write(f"data: {json.dumps(first_chunk)}\n\n".encode("utf-8"))
            self.wfile.flush()

        for line in resp:
            line_str = line.decode("utf-8", errors="ignore").strip()
            if not line_str:
                continue
            try:
                chunk_obj = json.loads(line_str)
            except Exception:
                continue

            delta_content = chunk_obj.get("message", {}).get("content", "")
            done = chunk_obj.get("done", False)

            openai_chunk = {
                "id": req_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": target_model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": delta_content} if delta_content else {},
                        "finish_reason": "stop" if done else None,
                    }
                ],
            }
            self.wfile.write(f"data: {json.dumps(openai_chunk)}\n\n".encode("utf-8"))
            self.wfile.flush()

        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def _handle_blocking_response(self, resp: Any, target_model: str, badge: str) -> None:
        """Handles single JSON payload response."""
        full_content = resp.read().decode("utf-8", errors="ignore")
        try:
            ollama_resp = json.loads(full_content)
            reply_text = badge + ollama_resp.get("message", {}).get("content", "")
        except Exception:
            reply_text = full_content

        openai_resp = {
            "id": f"chatcmpl-{int(time.time() * 1000)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": target_model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": reply_text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

        body = json.dumps(openai_resp).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy standard HTTP access logs; custom logger used instead
        pass


def run_smart_proxy(port: int = PROXY_DEFAULT_PORT, ollama_url: str = OLLAMA_DEFAULT_URL) -> None:
    """Runs the multi-threaded autonomous smart routing server."""
    SmartRouterHandler.ollama_url = ollama_url.rstrip("/")
    server = ThreadingHTTPServer(("127.0.0.1", port), SmartRouterHandler)
    logger.info("=" * 65)
    logger.info(" RTVS AUTONOMOUS SMART ROUTING PROXY ACTIVE")
    logger.info("=" * 65)
    logger.info(" Listening on:     http://127.0.0.1:%d/v1", port)
    logger.info(" Forwarding to:    %s", SmartRouterHandler.ollama_url)
    logger.info(" Unified Endpoint: 'rtvs-smart-router' (automatic natural language dispatch)")
    logger.info(" Targets:          Qwen3.8-27B | Qwen3:14B | Qwen2.5-Coder:32B | DeepSeek-R1")
    logger.info("=" * 65)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down smart router proxy.")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RTVS Autonomous Local AI Smart Router Proxy")
    parser.add_argument("--port", type=int, default=PROXY_DEFAULT_PORT, help="Port to listen on (default: 8000)")
    parser.add_argument("--ollama-url", type=str, default=OLLAMA_DEFAULT_URL, help="Ollama base URL (default: http://127.0.0.1:11434)")
    args = parser.parse_args()
    run_smart_proxy(port=args.port, ollama_url=args.ollama_url)

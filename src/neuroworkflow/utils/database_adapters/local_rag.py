"""
Local RAG / semantic search adapter for parameter metadata service.

Connects to a local RAG-based semantic search system (e.g. HyperRag) that indexes
papers and returns relevant snippets. Queries are formulated to retrieve short
answers with parameter values and references; an LLM curates the output into
the unified ParameterSuggestion format used by other adapters.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional

from .base import DatabaseAdapter
from ..parameter_metadata_service import ParameterSuggestion

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

# Source identifier for this adapter (aligned with other built-in sources)
LOCAL_RAG_SOURCE = "local_rag"


class LocalRAGAdapter(DatabaseAdapter):
    """
    Adapter for a local RAG/semantic search knowledge base.

    Expects an API that accepts a natural-language query and returns text chunks
    (and optionally metadata/sources). Typical endpoints: POST /query, /search,
    or /api/query with body like {"query": "..."} or {"question": "..."}.
    Response is normalized from common shapes (results, chunks, documents, data).
    LLM curation then extracts parameter values and references into
    ParameterSuggestion format.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = (self.config.get("base_url") or "").rstrip("/")
        self.query_endpoint = self.config.get("query_endpoint", "/query")
        if self.query_endpoint and not self.query_endpoint.startswith("/"):
            self.query_endpoint = "/" + self.query_endpoint
        self.timeout = self.config.get("timeout", 15)
        self.max_chunks = self.config.get("max_chunks", 10)
        self.source_label = self.config.get("source_name", "Local RAG")
        # Authentication: optional login (username/password) or static api_key / token
        self.username = self.config.get("username", "").strip()
        self.password = self.config.get("password", "")
        self.login_endpoint = (self.config.get("login_endpoint") or "/login").strip()
        if self.login_endpoint and not self.login_endpoint.startswith("/"):
            self.login_endpoint = "/" + self.login_endpoint
        self._rag_token: Optional[str] = None

    def get_source_name(self) -> str:
        return LOCAL_RAG_SOURCE

    def is_available(self) -> bool:
        return (
            bool(self.enabled)
            and bool(self.base_url)
            and self.base_url.startswith(("http://", "https://"))
        )

    def query_parameter(
        self,
        parameter_name: str,
        parameter_description: str,
        species: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ParameterSuggestion]:
        """
        Query the local RAG for parameter-related snippets, then curate with LLM
        into ParameterSuggestion list.
        """
        if not self.is_available() or not REQUESTS_AVAILABLE:
            return []

        suggestions: List[ParameterSuggestion] = []
        try:
            query_text = self._build_query(
                parameter_name, parameter_description, species, context
            )
            chunks = self._query_rag(query_text)
            if not chunks:
                return []

            if self.openai_client:
                suggestions = self._curate_with_llm(
                    parameter_name,
                    parameter_description,
                    chunks,
                    species,
                )
            else:
                suggestions = self._extract_simple(
                    parameter_name, chunks, species
                )
        except Exception as e:
            logger.warning("Local RAG adapter error: %s", e, exc_info=True)

        return suggestions

    def _build_query(
        self,
        parameter_name: str,
        parameter_description: str,
        species: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Build a natural-language query for the RAG to return value + reference."""
        parts = [
            f"What is the typical or reported value for the parameter: {parameter_name}?"
        ]
        if parameter_description:
            parts.append(f"Context: {parameter_description}.")
        if species:
            parts.append(f"Species: {species}.")
        if context:
            if context.get("brain_region"):
                parts.append(f"Brain region: {context['brain_region']}.")
            if context.get("cell_type"):
                parts.append(f"Cell type: {context['cell_type']}.")
        parts.append("Return short excerpts that state a specific numerical value and its source (paper or reference).")
        return " ".join(parts)

    def _ensure_auth(self) -> Optional[str]:
        """
        Obtain a token for authenticated RAG API requests.
        - If the RAG has no login endpoint and username is set: use username as Bearer (backend trusts Bearer as username).
        - Else if login_endpoint is set: POST to login and use returned token.
        - Else if api_key is set: use it as token.
        """
        if self._rag_token:
            return self._rag_token
        # Many RAG backends (e.g. in-repo rag) use Bearer <username> with no separate login API
        use_username_as_bearer = self.config.get("use_username_as_bearer")
        if use_username_as_bearer is None:
            use_username_as_bearer = not (self.login_endpoint and self.login_endpoint.strip())
        if use_username_as_bearer and self.username:
            self._rag_token = self.username
            return self._rag_token
        # Login endpoint: POST and extract token from response
        if self.username and self.password and self.login_endpoint and REQUESTS_AVAILABLE:
            url = f"{self.base_url}{self.login_endpoint}"
            for body in (
                {"username": self.username, "password": self.password},
                {"user": self.username, "password": self.password},
                {"email": self.username, "password": self.password},
            ):
                try:
                    r = requests.post(
                        url,
                        json=body,
                        headers={"Content-Type": "application/json"},
                        timeout=self.timeout,
                    )
                    r.raise_for_status()
                    data = r.json() if r.content else {}
                    token = (
                        data.get("access_token")
                        or data.get("token")
                        or data.get("jwt")
                        or (data.get("data") or {}).get("token")
                        or (data.get("data") or {}).get("access_token")
                    )
                    if token:
                        self._rag_token = token
                        return token
                except Exception as e:
                    logger.debug("Local RAG login attempt failed: %s", e)
                    continue
        if self.config.get("api_key"):
            self._rag_token = self.config["api_key"]
            return self._rag_token
        return None

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers, including auth token if available."""
        headers = {"Content-Type": "application/json"}
        token = self._ensure_auth()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        elif self.config.get("api_key") and not self.username:
            auth_header = self.config.get("api_key_header", "X-API-Key")
            headers[auth_header] = self.config["api_key"]
        return headers

    def _query_rag(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Call the RAG API and normalize response into a list of {text, source, score}.
        Tries /global_query first (in-repo RAG style), then /query with common payloads.
        """
        headers = self._build_headers()

        # In-repo RAG (and similar) use POST /global_query with {query, top_k}; response has final_answer, relevant_docs
        global_query_url = f"{self.base_url}/global_query"
        try:
            r = requests.post(
                global_query_url,
                json={"query": query_text, "top_k": min(self.max_chunks, 20), "session_uuids": [], "comprehensive": False},
                headers=headers,
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
            # Accept response in common shapes (direct or under "data")
            payload = data if isinstance(data, dict) else {}
            if not payload.get("final_answer") and isinstance(payload.get("data"), dict):
                payload = payload["data"]
            chunks = self._normalize_global_query_response(payload)
            if chunks:
                logger.info(
                    "Local RAG: got %d chunks from /global_query (first chunk len=%d)",
                    len(chunks),
                    len(chunks[0].get("text", "") or ""),
                )
                return chunks
        except requests.exceptions.RequestException as e:
            logger.warning("Local RAG /global_query failed: %s (is RAG running? From Docker use base_url http://host.docker.internal:8006)", e)
        except (ValueError, KeyError) as e:
            logger.warning("Local RAG global_query response parse error: %s", e)

        url = f"{self.base_url}{self.query_endpoint}"
        payloads = [
            {"query": query_text},
            {"question": query_text},
            {"q": query_text},
        ]
        for payload in payloads:
            try:
                r = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                r.raise_for_status()
                data = r.json()
                return self._normalize_rag_response(data)
            except requests.exceptions.RequestException as e:
                logger.warning("Local RAG request failed with payload %s: %s", list(payload.keys()), e)
                continue
            except (ValueError, KeyError) as e:
                logger.debug("Local RAG response parse error: %s", e)
                continue

        try:
            r = requests.get(
                f"{self.base_url}{self.query_endpoint}",
                params={"query": query_text, "q": query_text},
                headers=headers,
                timeout=self.timeout,
            )
            r.raise_for_status()
            return self._normalize_rag_response(r.json())
        except Exception as e:
            logger.warning("Local RAG GET fallback failed: %s", e)

        return []

    def _normalize_global_query_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize in-repo RAG GlobalQueryResponse (final_answer, relevant_docs, supporting_data) into chunks."""
        chunks: List[Dict[str, Any]] = []
        # Main answer: try all common keys (API may use final_answer, synthesis, or camelCase)
        main_text = (
            data.get("final_answer")
            or data.get("finalAnswer")
            or data.get("synthesis")
            or data.get("answer")
            or ""
        )
        if isinstance(main_text, str) and main_text.strip():
            chunks.append({"text": main_text.strip(), "source": "synthesis", "score": None})
        for i, doc in enumerate(data.get("relevant_docs") or data.get("relevantDocs") or []):
            if isinstance(doc, str):
                chunks.append({"text": doc, "source": f"relevant_doc_{i}", "score": None})
            elif isinstance(doc, dict) and doc.get("text"):
                chunks.append({"text": doc["text"], "source": doc.get("source", f"doc_{i}"), "score": doc.get("score")})
        supp = data.get("supporting_data") or data.get("supportingData") or {}
        if isinstance(supp, dict):
            for i, item in enumerate(supp.get("references") or supp.get("chunks") or []):
                if isinstance(item, str):
                    chunks.append({"text": item, "source": None, "score": None})
                elif isinstance(item, dict) and item.get("text"):
                    chunks.append({"text": item["text"], "source": item.get("source"), "score": item.get("score")})
            # RAG returns all_document_data: list of { doc_name, supporting_data: { child_chunks, parent_chunks } }
            for doc_block in supp.get("all_document_data") or []:
                if not isinstance(doc_block, dict):
                    continue
                doc_name = doc_block.get("doc_name", "document")
                sub = doc_block.get("supporting_data") or {}
                for chunk_list_key in ("child_chunks", "parent_chunks"):
                    for j, item in enumerate((sub.get(chunk_list_key) or [])[:5]):
                        text = None
                        if isinstance(item, str):
                            text = item
                        elif isinstance(item, dict):
                            text = item.get("text") or item.get("content") or item.get("body")
                        if text and isinstance(text, str) and text.strip():
                            chunks.append({"text": text.strip(), "source": doc_name, "score": None})
        elif isinstance(supp, list):
            for i, item in enumerate(supp[: self.max_chunks]):
                if isinstance(item, str):
                    chunks.append({"text": item, "source": None, "score": None})
                elif isinstance(item, dict) and item.get("text"):
                    chunks.append({"text": item["text"], "source": item.get("source"), "score": item.get("score")})
        return chunks[: self.max_chunks]

    def _normalize_rag_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract list of {text, source, score} from various response shapes."""
        chunks: List[Dict[str, Any]] = []
        raw = (
            data.get("results")
            or data.get("chunks")
            or data.get("documents")
            or data.get("data")
            or data.get("items")
            or []
        )
        if isinstance(data, list):
            raw = data

        for i, item in enumerate(raw[: self.max_chunks]):
            if isinstance(item, str):
                chunks.append({"text": item, "source": None, "score": None})
                continue
            if not isinstance(item, dict):
                continue
            text = (
                item.get("text")
                or item.get("content")
                or item.get("body")
                or item.get("abstract")
                or ""
            )
            if not text and "metadata" in item:
                meta = item["metadata"]
                if isinstance(meta, dict):
                    text = meta.get("text") or meta.get("content") or ""
                else:
                    text = str(meta)
            if not text:
                continue
            meta = item.get("metadata") or {}
            if isinstance(meta, dict):
                source = meta.get("source") or meta.get("citation") or meta.get("title") or meta.get("file_name")
            else:
                source = None
            score = item.get("score") if isinstance(item.get("score"), (int, float)) else None
            chunks.append({"text": text, "source": source, "score": score})

        return chunks

    def _curate_with_llm(
        self,
        parameter_name: str,
        parameter_description: str,
        chunks: List[Dict[str, Any]],
        species: Optional[str],
    ) -> List[ParameterSuggestion]:
        """Use LLM to turn RAG chunks into ParameterSuggestion list."""
        if not self.openai_client or not chunks:
            return []

        combined = ""
        for i, c in enumerate(chunks):
            combined += f"[Excerpt {i + 1}]"
            if c.get("source"):
                combined += f" (Source: {c['source']})\n"
            else:
                combined += "\n"
            combined += c["text"] + "\n\n"

        prompt = f"""You are extracting numerical parameter values from neuroscience literature excerpts (from a local RAG/knowledge base).

Parameter name: {parameter_name}
Parameter description: {parameter_description}
Species: {species or 'not specified'}

Excerpts from the knowledge base:

{combined}

Task: Extract every numerical value that clearly refers to this parameter (e.g. dendrite diameter in μm, conductance in nS). Include numbers even when wording is indirect (e.g. "dendrites were 0.8 μm", "mean diameter 1.2 μm").
1. Extract the exact numerical value (number).
2. Note units if mentioned (e.g. mV, Hz, μm, µm).
3. Use the excerpt's source/reference as citation when available; otherwise "From synthesis" or "From excerpt N".
4. Assign a confidence (0.0–1.0) based on how clearly the value is stated (0.5+ if units match the parameter).

Return a JSON object with this structure only:
{{
  "values": [
    {{
      "value": <number>,
      "units": "<string or empty>",
      "citation": "<source/reference>",
      "confidence": <0.0–1.0>,
      "context": "<brief context from text>"
    }}
  ]
}}

If the text contains numbers with relevant units (e.g. μm for diameter), include them. Only return {{ "values": [] }} if there is no number that could be this parameter.
Return only valid JSON, no other text."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You extract numerical parameter values from neuroscience text. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=800,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content.strip()
            data = json.loads(content)
        except Exception as e:
            logger.warning("Local RAG LLM curation failed: %s", e)
            return []

        suggestions = []
        for item in data.get("values", []):
            try:
                value = item.get("value")
                if value is None:
                    continue
                value = float(value)
            except (TypeError, ValueError):
                continue
            units = item.get("units") or ""
            citation = item.get("citation") or "Local RAG knowledge base"
            confidence = float(item.get("confidence", 0.65))
            context_str = item.get("context") or ""
            description = "Value from local RAG knowledge base (semantic search)."
            if units:
                description += f" Units: {units}."
            if context_str:
                description += f" {context_str[:200]}."

            suggestions.append(
                ParameterSuggestion(
                    value=value,
                    source=LOCAL_RAG_SOURCE,
                    confidence=min(1.0, max(0.0, confidence)),
                    description=description.strip(),
                    species=species,
                    citation=citation,
                    metadata={"units": units, "source_label": self.source_label},
                )
            )

        logger.info("Local RAG: LLM curation returned %d suggestions", len(suggestions))
        # If no structured values but we have synthesis text, try single-value LLM fallback then regex
        if not suggestions and chunks:
            synthesis_chunk = next((c for c in chunks if c.get("source") == "synthesis"), chunks[0])
            text = (synthesis_chunk.get("text") or "").strip()
            if len(text) > 200:
                logger.info("Local RAG: trying fallback single-value LLM extraction")
                fallback = self._curate_fallback_single_value(
                    parameter_name, parameter_description, text, species
                )
                if fallback:
                    suggestions.append(fallback)
                    logger.info("Local RAG: fallback single-value extraction added 1 suggestion")
                else:
                    # Last resort: regex for numbers with μm/um/diameter in text
                    regex_suggestions = self._extract_numbers_regex(
                        parameter_name, text, "Local RAG synthesis"
                    )
                    if regex_suggestions:
                        suggestions.extend(regex_suggestions[:3])  # cap at 3
                        logger.info("Local RAG: regex extraction added %d suggestion(s)", len(regex_suggestions[:3]))
        return suggestions

    def _curate_fallback_single_value(
        self,
        parameter_name: str,
        parameter_description: str,
        text: str,
        species: Optional[str],
    ) -> Optional[ParameterSuggestion]:
        """When the main curation returns 0 values, try to extract one number from synthesis text."""
        if not self.openai_client or not text:
            return None
        prompt = f"""From the following neuroscience text, extract ONE numerical value that best matches the parameter "{parameter_name}" ({parameter_description}). Species context: {species or 'any'}.

Text:
{text[:4000]}

Return JSON only: {{ "value": <number>, "units": "<e.g. μm or empty>", "citation": "<short source from text>" }}.
If no suitable number is found, return {{ "value": null }}."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract one number from text. Return only JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=200,
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content.strip())
            val = data.get("value")
            if val is None:
                return None
            value = float(val)
            units = (data.get("units") or "").strip()
            citation = (data.get("citation") or "Local RAG synthesis").strip()
            return ParameterSuggestion(
                value=value,
                source=LOCAL_RAG_SOURCE,
                confidence=0.6,
                description="Value from local RAG (fallback extraction)." + (f" Units: {units}." if units else ""),
                species=species,
                citation=citation,
                metadata={"units": units, "source_label": self.source_label},
            )
        except Exception as e:
            logger.warning("Local RAG fallback LLM extraction failed: %s", e)
            return None

    def _extract_numbers_regex(
        self,
        parameter_name: str,
        text: str,
        source_label: str,
    ) -> List[ParameterSuggestion]:
        """Extract numbers that look like parameter values (e.g. 0.5 μm) from text when LLM returns nothing."""
        suggestions: List[ParameterSuggestion] = []
        # Match numbers followed by μm, um, µm, or "micrometer" (diameter-like)
        patterns = [
            # 0.8 μm, 1.2 µm, 0.5 um (most reliable)
            re.compile(r"(\d+\.?\d*)\s*(?:μm|µm|um|micrometer|micrometre)s?\b", re.IGNORECASE),
            # diameter/dendrite within ~60 chars of number
            re.compile(
                rf"(?:diameter|dendrite|{re.escape(parameter_name.replace('_', ' '))})[^0-9]{{0,60}}(\d+\.?\d*)\s*(?:μm|µm|um)?",
                re.IGNORECASE,
            ),
            # number then μm within a few words
            re.compile(r"\b(\d+\.\d+)\s*(?:μm|µm|um)\b", re.IGNORECASE),
        ]
        seen: set = set()
        for pattern in patterns:
            for m in pattern.finditer(text):
                try:
                    val = float(m.group(1))
                    if val in seen:
                        continue
                    if not (0.001 <= val <= 1e3):  # plausible for diameters in μm
                        continue
                    seen.add(val)
                    units = "μm"
                    suggestions.append(
                        ParameterSuggestion(
                            value=val,
                            source=LOCAL_RAG_SOURCE,
                            confidence=0.55,
                            description="Value from local RAG (regex extraction from synthesis).",
                            species=None,
                            citation=source_label,
                            metadata={"units": units, "source_label": self.source_label},
                        )
                    )
                except (ValueError, IndexError):
                    continue
        return suggestions

    def _extract_simple(
        self,
        parameter_name: str,
        chunks: List[Dict[str, Any]],
        species: Optional[str],
    ) -> List[ParameterSuggestion]:
        """Simple numeric extraction when LLM is not available."""
        suggestions = []
        param_phrase = parameter_name.replace("_", " ")
        pattern = re.compile(
            rf"{re.escape(param_phrase)}\s*[:\-=]?\s*(?:was|is|of|about)?\s*(\d+\.?\d*)\s*(?:μm|nm|mm|mV|ms|Hz|pA|MΩ|μM|mM)?",
            re.IGNORECASE,
        )
        for c in chunks:
            text = c.get("text") or ""
            source = c.get("source") or "Local RAG"
            for m in pattern.findall(text):
                try:
                    val = float(m)
                    if 0.001 <= abs(val) <= 1e6:
                        suggestions.append(
                            ParameterSuggestion(
                                value=val,
                                source=LOCAL_RAG_SOURCE,
                                confidence=0.5,
                                description="Value extracted from local RAG (no LLM).",
                                species=species,
                                citation=str(source),
                                metadata={"source_label": self.source_label},
                            )
                        )
                        break
                except ValueError:
                    continue
        return suggestions

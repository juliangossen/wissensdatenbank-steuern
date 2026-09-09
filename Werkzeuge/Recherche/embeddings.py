"""Local, versioned German-capable semantic embeddings, without API calls.

Only the public model files are downloaded. Document and query texts stay local.
Search chunks are separate from the unmodified, complete provision used by fetch.
"""

from __future__ import annotations

import hashlib
import math
import os
import threading
from collections import deque
from concurrent.futures import ProcessPoolExecutor
from itertools import chain, islice
import multiprocessing
from pathlib import Path
from typing import Any, Iterable, Iterator


MODEL_NAME = "intfloat/multilingual-e5-small"
MODEL_COMMIT = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
MODEL_FILE = "onnx/model_qint8_avx512_vnni.onnx"
MODEL_SHA256 = "dd476dd0c2514e9b9be83aeb3853fac0763e0bdf4a71645407587d77c48a2d88"
MAX_INPUT_TOKENS = 512
CHUNKER_VERSION = "e5-token-offsets-v1-448-48"
_MODEL_REGISTRATION_LOCK = threading.Lock()
_PROCESS_EMBEDDER = None


class EmbeddingError(RuntimeError):
    """The real local model could not be loaded or returned invalid results."""


def _initialize_embedding_process(cache_dir: str) -> None:
    """Each bounded worker owns its CPU model; no database is opened here."""
    global _PROCESS_EMBEDDER
    _PROCESS_EMBEDDER = LocalEmbedder(Path(cache_dir))
    _PROCESS_EMBEDDER._load()


def _embed_process_batch(texts: list[str]) -> list[list[float]]:
    if _PROCESS_EMBEDDER is None:
        raise EmbeddingError("Lokaler Embedding-Arbeitsprozess wurde nicht initialisiert.")
    return _PROCESS_EMBEDDER.embed_documents(texts)


def chunk_text(text: str, max_chars: int = 1600, overlap_chars: int = 160) -> list[str]:
    """Character-only helper; use LocalEmbedder.chunk_text for model-safe chunks.

    Keeps all characters, including whitespace. This helper does not promise a
    tokenizer limit: character counts cannot reliably approximate German tokens.
    """
    if max_chars < 1 or not 0 <= overlap_chars < max_chars:
        raise ValueError("max_chars muss positiv und overlap_chars kleiner sein.")
    if not text.strip():
        return []
    result: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        result.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap_chars
    return result


class LocalEmbedder:
    """CPU embeddings with a pinned public ONNX model, loaded on first use.

    ``chunk_text(body, title=title)`` returns body chunks. Embed each as
    ``title + '\n' + chunk`` (or just chunk when title is empty). E5's required
    ``passage:`` and ``query:`` prefixes are added here, exactly once.
    """

    model_name = MODEL_NAME
    model_revision = f"{MODEL_COMMIT}:{MODEL_FILE}:prefix-v1:{CHUNKER_VERSION}"
    dimensions = 384
    max_input_tokens = MAX_INPUT_TOKENS

    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir).resolve()
        self._model: Any = None
        self._tokenizer: Any = None
        self._load_lock = threading.Lock()
        self._inference_lock = threading.Lock()

    def _load(self) -> None:
        if self._model is not None:
            return
        with self._load_lock:
            if self._model is not None:
                return
            try:
                from fastembed import TextEmbedding
                from fastembed.common.model_description import ModelSource, PoolingType
                from huggingface_hub import snapshot_download
                from tokenizers import Tokenizer

                self.cache_dir.mkdir(parents=True, exist_ok=True)
                files = [
                    "config.json", "tokenizer.json", "tokenizer_config.json",
                    "special_tokens_map.json", MODEL_FILE,
                ]
                # Pin via Hugging Face itself, then pass that exact local path.
                # FastEmbed's default model download may otherwise track main.
                download_args = dict(
                    repo_id=MODEL_NAME, revision=MODEL_COMMIT,
                    cache_dir=str(self.cache_dir), allow_patterns=files,
                    token=False,
                )
                try:
                    model_dir = Path(snapshot_download(**download_args, local_files_only=True))
                    if not all((model_dir / name).is_file() for name in files):
                        raise FileNotFoundError("Modellcache ist unvollständig.")
                except (OSError, ValueError):
                    model_dir = Path(snapshot_download(**download_args))
                with (model_dir / MODEL_FILE).open("rb") as handle:
                    actual_hash = hashlib.file_digest(handle, "sha256").hexdigest()
                if actual_hash != MODEL_SHA256:
                    raise EmbeddingError("Die SHA-256-Prüfung des Embedding-Modells ist fehlgeschlagen.")
                with _MODEL_REGISTRATION_LOCK:
                    registered = {entry["model"] for entry in TextEmbedding.list_supported_models()}
                    # A unique name prevents a future built-in definition from
                    # silently choosing different pooling or a different file.
                    registered_name = f"{MODEL_NAME}-kb-qint8-{MODEL_COMMIT[:12]}"
                    if registered_name not in registered:
                        TextEmbedding.add_custom_model(
                            model=registered_name, pooling=PoolingType.MEAN,
                            normalization=True, dim=self.dimensions,
                            sources=ModelSource(hf=MODEL_NAME),
                            model_file=MODEL_FILE,
                        )
                model = TextEmbedding(
                    model_name=registered_name,
                    specific_model_path=str(model_dir),
                    cache_dir=str(self.cache_dir),
                    providers=["CPUExecutionProvider"],
                    threads=min(4, os.cpu_count() or 1),
                    local_files_only=True,
                )
                tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
                tokenizer.no_truncation()
                tokenizer.no_padding()
                # Disable FastEmbed's truncation too: our explicit validation
                # below is the sole limit and can never conceal a lost tail.
                model.model.tokenizer.no_truncation()
                self._tokenizer = tokenizer
                self._model = model
            except EmbeddingError:
                raise
            except Exception as exc:
                raise EmbeddingError(
                    "Das lokale Embedding-Modell konnte nicht geladen werden. "
                    "Beim ersten Start werden etwa 136 MB öffentliche Modelldateien "
                    "benötigt; anschließend funktioniert der Cache offline. "
                    "Es wurde kein Ersatzvektor und kein externer KI-Dienst verwendet. "
                    f"Ursache: {exc}"
                ) from exc

    def token_count(self, text: str, *, query: bool = False) -> int:
        """Count actual model tokens including special tokens and E5 prefix."""
        self._load()
        prefix = "query: " if query else "passage: "
        return len(self._tokenizer.encode(prefix + text).ids)

    def chunk_text(
        self, text: str, title: str = "", *, max_tokens: int = 448,
        overlap_tokens: int = 48, query: bool = False,
    ) -> list[str]:
        """Split all input by real token offsets, with title and prefix budget.

        Returns exact substrings of ``text``. Default windows contain at most
        448 total model tokens (including title, E5 prefix and special tokens),
        with up to 48 body tokens overlapping. Every non-whitespace character
        is covered. Full legal text and footnotes must still be stored separately.
        """
        if not text.strip():
            return []
        if not 8 <= max_tokens <= MAX_INPUT_TOKENS:
            raise ValueError(f"max_tokens muss zwischen 8 und {MAX_INPUT_TOKENS} liegen.")
        if not 0 <= overlap_tokens < max_tokens:
            raise ValueError("overlap_tokens muss kleiner als max_tokens sein.")
        self._load()
        heading = title + "\n" if title else ""
        prefix_cost = self.token_count(heading, query=query)
        # Two tokens reserve possible retokenization changes at slice edges.
        body_budget = max_tokens - prefix_cost - 2
        if body_budget < 8 or overlap_tokens >= body_budget:
            raise ValueError("Der Titel ist für das gewählte Tokenfenster zu lang.")
        if self.token_count(heading + text, query=query) <= max_tokens:
            return [text]
        encoded = self._tokenizer.encode(text, add_special_tokens=False)
        offsets = encoded.offsets
        if not offsets:
            return [text]
        pieces: list[str] = []
        token_start = 0
        char_start = 0
        while token_start < len(offsets):
            token_end = min(len(offsets), token_start + body_budget)
            char_end = len(text) if token_end == len(offsets) else offsets[token_end][0]
            while self.token_count(heading + text[char_start:char_end], query=query) > max_tokens:
                token_end -= 1
                if token_end <= token_start:
                    raise EmbeddingError("Der Text kann nicht verlustfrei in Tokenfenster zerlegt werden.")
                char_end = offsets[token_end][0]
            pieces.append(text[char_start:char_end])
            if token_end == len(offsets):
                break
            next_token = max(token_start + 1, token_end - overlap_tokens)
            next_char = offsets[next_token][0]
            # Some Unicode token offsets repeat; progress must remain explicit.
            while next_token < token_end and next_char <= char_start:
                next_token += 1
                next_char = offsets[next_token][0]
            token_start, char_start = next_token, next_char
        return pieces

    def _embed(self, texts: list[str], *, query: bool) -> list[list[float]]:
        if not texts:
            return []
        self._load()
        prefix = "query: " if query else "passage: "
        prepared: list[str] = []
        for index, text in enumerate(texts):
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"Embedding-Text {index} ist leer oder kein Text.")
            count = self.token_count(text, query=query)
            if count > MAX_INPUT_TOKENS:
                raise ValueError(
                    f"Embedding-Text {index} hat {count} Token; höchstens {MAX_INPUT_TOKENS} "
                    "sind erlaubt. Vorher LocalEmbedder.chunk_text mit Titel verwenden."
                )
            prepared.append(prefix + text)
        try:
            with self._inference_lock:
                vectors = [vector.tolist() for vector in self._model.embed(prepared, batch_size=32)]
        except Exception as exc:
            raise EmbeddingError(f"Lokale Embedding-Berechnung fehlgeschlagen: {exc}") from exc
        if len(vectors) != len(texts):
            raise EmbeddingError("Die Anzahl der Embeddings passt nicht zur Anzahl der Texte.")
        for vector in vectors:
            if len(vector) != self.dimensions or not all(math.isfinite(v) for v in vector):
                raise EmbeddingError("Das Modell lieferte einen ungültigen Embedding-Vektor.")
            if not 0.99 < math.sqrt(sum(v * v for v in vector)) < 1.01:
                raise EmbeddingError("Der Embedding-Vektor ist nicht normalisiert.")
        return vectors

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts, query=False)

    def embed_document_batches(
        self, batches: Iterable[list[str]], *, workers: int = 2,
    ) -> Iterator[list[list[float]]]:
        """Yield input-order batches from two bounded local CPU processes.

        Every worker uses the same pinned model, four inference threads, E5
        prefix and input validation as serial inference. At most ``workers``
        batches are in flight; the caller alone persists each verified result.
        Two workers keep full 32-text windows within the measured memory budget.
        Completed prior batches remain usable if a later worker fails.
        """
        if not isinstance(workers, int) or not 1 <= workers <= 4:
            raise ValueError("workers muss zwischen 1 und 4 liegen.")
        source = iter(batches)
        initial = list(islice(source, workers))
        if workers == 1 or len(initial) < 2:
            for batch in chain(initial, source):
                yield self.embed_documents(batch)
            return
        self._load()
        executor = ProcessPoolExecutor(
            max_workers=min(workers, len(initial)),
            mp_context=multiprocessing.get_context("spawn"),
            initializer=_initialize_embedding_process,
            initargs=(str(self.cache_dir),),
        )
        pending = deque()
        exhausted = object()
        try:
            pending.extend(executor.submit(_embed_process_batch, batch) for batch in initial)
            while pending:
                future = pending.popleft()
                try:
                    vectors = future.result()
                except Exception as exc:
                    raise EmbeddingError(f"Parallele lokale Embedding-Berechnung fehlgeschlagen: {exc}") from exc
                # Refill before yielding so parent-only SQLite verification and
                # persistence can overlap the next CPU batch without reordering.
                following = next(source, exhausted)
                if following is not exhausted:
                    pending.append(executor.submit(_embed_process_batch, following))
                yield vectors
        finally:
            for future in pending:
                future.cancel()
            executor.shutdown(wait=True, cancel_futures=True)

    def embed_query(self, text: str) -> list[float]:
        """Embed a question; long questions use normalized mean of all windows."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Die Suchfrage darf nicht leer sein.")
        chunks = self.chunk_text(text, query=True)
        vectors = self._embed(chunks, query=True)
        if len(vectors) == 1:
            return vectors[0]
        mean = [sum(column) / len(vectors) for column in zip(*vectors)]
        norm = math.sqrt(sum(v * v for v in mean))
        if not norm:
            raise EmbeddingError("Die lange Suchfrage ergibt keinen gültigen Gesamtvektor.")
        return [value / norm for value in mean]

"""
RAVEN Firebase Admin SDK Connection & Local Emulator Gateway

Provides Firestore client access via official `firebase-admin` SDK when credentials
are present, or falls back seamlessly to a thread-safe, document-structured Firestore
emulator for offline testing and local demo environments.
"""

import os
import threading
import time
from typing import Any, Callable, Generator


class FirestoreDocSnapshot:
    """Snapshot representing a single Firestore document."""

    def __init__(self, doc_id: str, data: dict[str, Any] | None, exists: bool = True) -> None:
        self.id = doc_id
        self._data = data or {}
        self.exists = exists

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)

    def get(self, field: str) -> Any:
        return self._data.get(field)


class FirestoreQuery:
    """Query builder for Firestore document collections."""

    def __init__(self, docs: dict[str, dict[str, Any]]) -> None:
        self._docs = docs
        self._filters: list[tuple[str, str, Any]] = []
        self._order_by: tuple[str, bool] | None = None
        self._limit: int | None = None

    def where(self, field: str, op: str, value: Any) -> "FirestoreQuery":
        query = FirestoreQuery(self._docs)
        query._filters = self._filters + [(field, op, value)]
        query._order_by = self._order_by
        query._limit = self._limit
        return query

    def order_by(self, field: str, direction: str = "ASCENDING") -> "FirestoreQuery":
        query = FirestoreQuery(self._docs)
        query._filters = list(self._filters)
        query._order_by = (field, direction.upper() == "DESCENDING")
        query._limit = self._limit
        return query

    def limit(self, n: int) -> "FirestoreQuery":
        query = FirestoreQuery(self._docs)
        query._filters = list(self._filters)
        query._order_by = self._order_by
        query._limit = n
        return query

    def stream(self) -> Generator[FirestoreDocSnapshot, None, None]:
        matched: list[tuple[str, dict[str, Any]]] = []

        for doc_id, data in self._docs.items():
            match = True
            for field, op, val in self._filters:
                doc_val = data.get(field)
                if op == "==":
                    if doc_val != val:
                        match = False
                elif op == "!=":
                    if doc_val == val:
                        match = False
                elif op == ">":
                    if doc_val is None or doc_val <= val:
                        match = False
                elif op == ">=":
                    if doc_val is None or doc_val < val:
                        match = False
                elif op == "<":
                    if doc_val is None or doc_val >= val:
                        match = False
                elif op == "<=":
                    if doc_val is None or doc_val > val:
                        match = False
                elif op == "in":
                    if doc_val not in val:
                        match = False
                elif op == "array-contains":
                    if not isinstance(doc_val, list) or val not in doc_val:
                        match = False
            if match:
                matched.append((doc_id, dict(data)))

        if self._order_by:
            field, reverse = self._order_by
            matched.sort(key=lambda item: item[1].get(field, ""), reverse=reverse)

        if self._limit is not None:
            matched = matched[: self._limit]

        for doc_id, data in matched:
            yield FirestoreDocSnapshot(doc_id, data, exists=True)

    def get(self) -> list[FirestoreDocSnapshot]:
        return list(self.stream())


class FirestoreDocumentRef:
    """Document reference pointing to a specific document inside a collection."""

    def __init__(self, collection: "FirestoreCollectionRef", doc_id: str) -> None:
        self.collection = collection
        self.id = doc_id

    def get(self) -> FirestoreDocSnapshot:
        return self.collection._get_doc(self.id)

    def set(self, data: dict[str, Any], merge: bool = False) -> None:
        self.collection._set_doc(self.id, data, merge=merge)

    def update(self, data: dict[str, Any]) -> None:
        self.collection._update_doc(self.id, data)

    def delete(self) -> None:
        self.collection._delete_doc(self.id)


class FirestoreCollectionRef:
    """Collection reference holding document instances."""

    def __init__(self, store: "FirestoreEmulator", collection_name: str) -> None:
        self._store = store
        self.name = collection_name

    def document(self, doc_id: str | None = None) -> FirestoreDocumentRef:
        target_id = doc_id or f"doc_{int(time.time() * 1000)}_{len(self._store._data.get(self.name, {})) + 1}"
        return FirestoreDocumentRef(self, target_id)

    def _get_docs_dict(self) -> dict[str, dict[str, Any]]:
        with self._store._lock:
            col_data = self._store._data.get(self.name, {})
            return dict(col_data)

    def _get_doc(self, doc_id: str) -> FirestoreDocSnapshot:
        with self._store._lock:
            col_data = self._store._data.get(self.name, {})
            if doc_id in col_data:
                return FirestoreDocSnapshot(doc_id, dict(col_data[doc_id]), exists=True)
            return FirestoreDocSnapshot(doc_id, None, exists=False)

    def _set_doc(self, doc_id: str, data: dict[str, Any], merge: bool = False) -> None:
        with self._store._lock:
            if self.name not in self._store._data:
                self._store._data[self.name] = {}
            if merge and doc_id in self._store._data[self.name]:
                self._store._data[self.name][doc_id].update(dict(data))
            else:
                self._store._data[self.name][doc_id] = dict(data)

    def _update_doc(self, doc_id: str, data: dict[str, Any]) -> None:
        with self._store._lock:
            if self.name in self._store._data and doc_id in self._store._data[self.name]:
                self._store._data[self.name][doc_id].update(dict(data))

    def _delete_doc(self, doc_id: str) -> None:
        with self._store._lock:
            if self.name in self._store._data:
                self._store._data[self.name].pop(doc_id, None)

    def where(self, field: str, op: str, value: Any) -> FirestoreQuery:
        return FirestoreQuery(self._get_docs_dict()).where(field, op, value)

    def order_by(self, field: str, direction: str = "ASCENDING") -> FirestoreQuery:
        return FirestoreQuery(self._get_docs_dict()).order_by(field, direction)

    def limit(self, n: int) -> FirestoreQuery:
        return FirestoreQuery(self._get_docs_dict()).limit(n)

    def stream(self) -> Generator[FirestoreDocSnapshot, None, None]:
        return FirestoreQuery(self._get_docs_dict()).stream()

    def get(self) -> list[FirestoreDocSnapshot]:
        return list(self.stream())

    def add(self, data: dict[str, Any]) -> tuple[Any, FirestoreDocumentRef]:
        doc_ref = self.document()
        doc_ref.set(data)
        return (None, doc_ref)


class FirestoreTransaction:
    """Simulated atomic transaction context."""

    def __init__(self, emulator: "FirestoreEmulator") -> None:
        self._emulator = emulator

    def get(self, doc_ref: FirestoreDocumentRef) -> FirestoreDocSnapshot:
        return doc_ref.get()

    def set(self, doc_ref: FirestoreDocumentRef, data: dict[str, Any], merge: bool = False) -> None:
        doc_ref.set(data, merge=merge)

    def update(self, doc_ref: FirestoreDocumentRef, data: dict[str, Any]) -> None:
        doc_ref.update(data)

    def delete(self, doc_ref: FirestoreDocumentRef) -> None:
        doc_ref.delete()


class FirestoreEmulator:
    """Thread-safe in-memory Firestore emulator for testing & offline mode."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict[str, dict[str, dict[str, Any]]] = {}

    def collection(self, collection_name: str) -> FirestoreCollectionRef:
        return FirestoreCollectionRef(self, collection_name)

    def transaction(self) -> FirestoreTransaction:
        return FirestoreTransaction(self)

    def run_transaction(self, callback: Callable[[FirestoreTransaction], Any]) -> Any:
        with self._lock:
            txn = FirestoreTransaction(self)
            return callback(txn)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


_firebase_db_instance: Any = None
_firebase_initialized = False
_emulator_instance = FirestoreEmulator()


def get_firestore_client() -> Any:
    """
    Returns live Firestore client via `firebase_admin` if credentials exist,
    otherwise returns thread-safe `FirestoreEmulator`.
    """
    global _firebase_db_instance, _firebase_initialized

    if _firebase_db_instance is not None and _firebase_db_instance is not _emulator_instance:
        return _firebase_db_instance

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    cred_raw = (
        os.getenv("FIREBASE_CREDENTIALS_JSON")
        or os.getenv("FIREBASE_CREDENTIALS")
        or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    )
    project_id = os.getenv("FIREBASE_PROJECT_ID")

    # Auto-detect default service account JSON file in workspace root if present
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_service_account = os.path.join(repo_root, "firebase_service_account.json")
    if (not cred_raw or not os.path.exists(cred_raw)) and os.path.exists(root_service_account):
        cred_raw = root_service_account

    if cred_raw or project_id:
        try:
            import base64
            import json
            import firebase_admin  # type: ignore[import-untyped]
            from firebase_admin import credentials, firestore  # type: ignore[import-untyped]

            if not firebase_admin._apps:
                cred_obj = None
                if cred_raw:
                    s = cred_raw.strip()
                    # 1. Direct JSON string
                    if s.startswith("{") and s.endswith("}"):
                        try:
                            cred_obj = credentials.Certificate(json.loads(s))
                        except Exception:
                            pass
                    # 2. Base64 encoded JSON string
                    if cred_obj is None:
                        try:
                            decoded = base64.b64decode(s).decode("utf-8").strip()
                            if decoded.startswith("{") and decoded.endswith("}"):
                                cred_obj = credentials.Certificate(json.loads(decoded))
                        except Exception:
                            pass
                    # 3. File path (relative or absolute)
                    if cred_obj is None:
                        if os.path.exists(s):
                            cred_obj = credentials.Certificate(s)
                        else:
                            abs_p = os.path.abspath(s)
                            if os.path.exists(abs_p):
                                cred_obj = credentials.Certificate(abs_p)

                if cred_obj:
                    firebase_admin.initialize_app(cred_obj, {"projectId": project_id} if project_id else None)
                else:
                    # No credential object could be loaded; fall back cleanly without noisy ADC warnings
                    _firebase_db_instance = _emulator_instance
                    return _firebase_db_instance

            _firebase_db_instance = firestore.client()
            _firebase_initialized = True
            print(f"[FIREBASE] Connected to live Cloud Firestore (Project: {project_id or 'default'})")
            return _firebase_db_instance
        except Exception as err:
            print(f"[FIREBASE WARNING] Failed to connect to live Firestore ({err}). Falling back to emulator.")

    _firebase_db_instance = _emulator_instance
    return _firebase_db_instance


def reset_firestore_emulator() -> None:
    """Resets emulator state (for testing)."""
    _emulator_instance.clear()

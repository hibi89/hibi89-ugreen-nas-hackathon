"""Redacted, read-only DBVORA P0 contract for disposable LA SQLite ONLY.

The source DBVORA implementation remains in its own private repository. This
public bridge accepts an injected inventory callable, never imports/embeds
DBVORA code, does not open rows or enumerate customer databases, and NEVER
returns table/column names, database identifiers, source paths or timestamps.
The injection being valid does not establish provenance of the private source.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import stat
from typing import Callable, Any


class DBVORABridgeRefused(ValueError):
    """Fail-closed error without source paths or raw database metadata."""


MAX_SYNTHETIC_LEDGER_BYTES = 2 * 1024 * 1024


def _synthetic_ledger_digest(path: Path) -> str:
    """Hash only the disposable LA SQLite file, never user-selected files."""
    with path.open("rb") as stream:
        content = stream.read(MAX_SYNTHETIC_LEDGER_BYTES + 1)
    if not 100 <= len(content) <= MAX_SYNTHETIC_LEDGER_BYTES:
        raise DBVORABridgeRefused("DBVORA_SYNTHETIC_LEDGER_SIZE_REFUSED")
    return hashlib.sha256(content).hexdigest()


def summarize_synthetic_dbvora_inventory(raw: object) -> dict[str, Any]:
    """Accept only the known P0 SQLite metadata contract, redact all names."""
    if (type(raw) is not dict
            or raw.get("contract_version") != "p0-01.v1"
            or raw.get("engine") != "sqlite"
            or type(raw.get("size_bytes")) is not int
            or raw["size_bytes"] < 100
            or raw.get("size_scope") != "main_database_file_only_excludes_wal_and_shm"):
        raise DBVORABridgeRefused("DBVORA_CONTRACT_MISMATCH")
    provenance = raw.get("provenance")
    if (type(provenance) is not dict
            or provenance.get("tables") != "measured_sqlite_catalog"
            or provenance.get("size_bytes") != "measured_local_filesystem"):
        raise DBVORABridgeRefused("DBVORA_PROVENANCE_UNVERIFIED")
    tables, relationships = raw.get("tables"), raw.get("relationships")
    if (type(tables) is not list or not 1 <= len(tables) <= 1000
            or type(relationships) is not list
            or len(relationships) > 100000):
        raise DBVORABridgeRefused("DBVORA_SCHEMA_BOUND_EXCEEDED")
    names: set[str] = set()
    columns = indexes = foreign_keys = 0
    for table in tables:
        if type(table) is not dict:
            raise DBVORABridgeRefused("DBVORA_TABLE_CONTRACT_MISMATCH")
        name = table.get("name")
        if type(name) is not str or not name or name in names:
            raise DBVORABridgeRefused("DBVORA_TABLE_CONTRACT_MISMATCH")
        names.add(name)
        for field in ("columns", "indexes", "foreign_keys"):
            if type(table.get(field)) is not list:
                raise DBVORABridgeRefused("DBVORA_TABLE_CONTRACT_MISMATCH")
        if any(type(c) is not dict or type(c.get("name")) is not str
               for c in table["columns"]):
            raise DBVORABridgeRefused("DBVORA_COLUMN_CONTRACT_MISMATCH")
        if any(type(i) is not dict or type(i.get("name")) is not str
               for i in table["indexes"]):
            raise DBVORABridgeRefused("DBVORA_INDEX_CONTRACT_MISMATCH")
        columns += len(table["columns"])
        indexes += len(table["indexes"])
        foreign_keys += len(table["foreign_keys"])
    # The only supported input is the disposable LA-generated business ledger.
    # A source inventory from an unrelated SQLite file must not be accepted.
    if "records" not in names:
        raise DBVORABridgeRefused("SYNTHETIC_LA_LEDGER_NOT_PRESENT")
    if any(type(row) is not dict or row.get("evidence") != "declared_foreign_key"
           for row in relationships):
        raise DBVORABridgeRefused("DBVORA_RELATIONSHIP_CONTRACT_MISMATCH")
    return {
        "status": "SYNTHETIC_SCHEMA_METADATA_ONLY",
        "contract": "ugreen-dbvora-p0-redacted.v1",
        "scope": "DISPOSABLE_LOCAL_LA_SQLITE_NOT_NAS",
        "table_count": len(tables),
        "column_count": columns,
        "index_count": indexes,
        "declared_foreign_key_count": foreign_keys,
        "relationship_count": len(relationships),
        "main_database_file_bytes": raw["size_bytes"],
        "source_implementation_independently_verified": False,
        "real_nas_or_customer_database_inspected": False,
    }


def inspect_disposable_la_ledger(path: Path, reader: Callable[[Path], dict]) -> dict:
    """Invoke supplied read-only metadata inspector ONLY on a temporary ledger."""
    if not callable(reader) or not isinstance(path, Path):
        raise DBVORABridgeRefused("DBVORA_SYNTHETIC_READER_UNAVAILABLE")
    # The caller must pass its own disposable LA business.sqlite. Refuse
    # symlink/reparse and multi-link paths before calling an injected reader.
    # This is a local preflight, NOT atomic protection against concurrent
    # replacement on an untrusted filesystem.
    try:
        info = path.lstat()
        if (path.name != "business.sqlite"
                or path.is_symlink() or path.parent.is_symlink()
                or not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1):
            raise DBVORABridgeRefused("DBVORA_SYNTHETIC_READER_UNAVAILABLE")
    except OSError:
        raise DBVORABridgeRefused("DBVORA_SYNTHETIC_READER_UNAVAILABLE") from None
    try:
        # Detection, not a transactional filesystem lock: the optional reader
        # must not alter bytes, file identity or mtime of synthetic LA SQLite.
        before = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
                  _synthetic_ledger_digest(path))
        inventory = reader(path)
        after_info = path.lstat()
        after = (after_info.st_dev, after_info.st_ino, after_info.st_size,
                 after_info.st_mtime_ns, _synthetic_ledger_digest(path))
        if before != after or path.is_symlink() or after_info.st_nlink != 1:
            raise DBVORABridgeRefused("DBVORA_SYNTHETIC_LEDGER_CHANGED")
    except DBVORABridgeRefused:
        raise
    except Exception:
        # Never propagate private source paths, SQL fragments or library errors.
        raise DBVORABridgeRefused("DBVORA_SYNTHETIC_INSPECTION_FAILED") from None
    return summarize_synthetic_dbvora_inventory(inventory)

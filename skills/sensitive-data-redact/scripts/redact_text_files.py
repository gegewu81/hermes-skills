#!/usr/bin/env python3
"""Preview or redact a literal secret in Hermes text files."""

from __future__ import annotations

import argparse
import getpass
import os
import stat
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MAX_BYTES = 64 * 1024 * 1024
REPLACEMENT = b"***REDACTED***"
TEXT_NAMES = frozenset({".env"})
TEXT_SUFFIXES = frozenset(
    {".json", ".jsonl", ".log", ".md", ".py", ".sh", ".txt", ".yaml", ".yml"}
)


@dataclass(frozen=True)
class SkippedFile:
    """A candidate that could not be checked safely."""

    path: Path
    reason: str


@dataclass(frozen=True)
class RedactionReport:
    """Result of one preview or apply pass."""

    matched_files: tuple[Path, ...]
    replacement_count: int
    skipped_files: tuple[SkippedFile, ...]


def _candidate_files(root: Path) -> tuple[list[Path], list[SkippedFile]]:
    candidates: list[Path] = []
    skipped_files: list[SkippedFile] = []
    for candidate in sorted(root.rglob("*")):
        if candidate.is_symlink():
            skipped_files.append(SkippedFile(candidate, "symbolic link"))
            continue
        if not candidate.is_file():
            continue
        if candidate.name in TEXT_NAMES or candidate.suffix.lower() in TEXT_SUFFIXES:
            candidates.append(candidate)
    return candidates, skipped_files


def _atomic_replace(destination: Path, content: bytes) -> None:
    original_mode = stat.S_IMODE(destination.stat().st_mode)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, original_mode)
        os.replace(temporary_path, destination)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def redact_tree(
    root: Path,
    secret: bytes,
    *,
    apply: bool,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> RedactionReport:
    """Find literal secret bytes and optionally replace them atomically."""

    if not secret:
        raise ValueError("Secret cannot be empty")
    if max_bytes <= 0:
        raise ValueError("Maximum file size must be positive")

    matched_files: list[Path] = []
    replacement_count = 0
    candidates, skipped_files = _candidate_files(root)

    for candidate in candidates:
        try:
            file_stat = candidate.stat()
            if file_stat.st_nlink != 1:
                skipped_files.append(
                    SkippedFile(candidate, "file has multiple hard links")
                )
                continue
            if file_stat.st_size > max_bytes:
                skipped_files.append(
                    SkippedFile(candidate, f"file exceeds {max_bytes} bytes")
                )
                continue
            content = candidate.read_bytes()
            content.decode("utf-8")
        except UnicodeDecodeError:
            skipped_files.append(SkippedFile(candidate, "file is not UTF-8 text"))
            continue
        except OSError as error:
            skipped_files.append(SkippedFile(candidate, str(error)))
            continue

        matches = content.count(secret)
        if matches == 0:
            continue
        matched_files.append(candidate)
        replacement_count += matches
        if apply:
            _atomic_replace(candidate, content.replace(secret, REPLACEMENT))

    return RedactionReport(
        matched_files=tuple(matched_files),
        replacement_count=replacement_count,
        skipped_files=tuple(skipped_files),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or redact a literal secret in Hermes text files."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.home() / ".hermes",
        help="Hermes directory to scan (default: ~/.hermes)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write replacements. Without this flag, only preview matches.",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_BYTES,
        help=f"Skip files larger than this size (default: {DEFAULT_MAX_BYTES}).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the redaction preview or apply command."""

    parser = _parser()
    arguments = parser.parse_args(argv)
    root = arguments.root.expanduser()
    if not root.is_dir():
        parser.error(f"Root is not a directory: {root}")

    secret_text = getpass.getpass("Secret to redact: ")
    if not secret_text:
        parser.error("Secret cannot be empty")

    report = redact_tree(
        root,
        secret_text.encode("utf-8"),
        apply=arguments.apply,
        max_bytes=arguments.max_bytes,
    )
    verb = "Redacted" if arguments.apply else "Found"
    print(
        f"{verb} {report.replacement_count} occurrence(s) "
        f"in {len(report.matched_files)} file(s)."
    )
    for matched_file in report.matched_files:
        print(f"  {matched_file}")
    for skipped_file in report.skipped_files:
        print(f"Skipped {skipped_file.path}: {skipped_file.reason}")
    return 2 if report.skipped_files else 0


if __name__ == "__main__":
    raise SystemExit(main())

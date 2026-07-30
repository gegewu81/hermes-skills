from __future__ import annotations

import importlib.util
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).parents[1]
    / "skills"
    / "sensitive-data-redact"
    / "scripts"
    / "redact_text_files.py"
)
SPEC = importlib.util.spec_from_file_location("redact_text_files", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load redaction helper")
redact_text_files = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = redact_text_files
SPEC.loader.exec_module(redact_text_files)


class RedactTreeTests(unittest.TestCase):
    def test_preview_counts_literal_secret_without_writing(self) -> None:
        secret = b"a/b[c].*?&"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown = root / "session.md"
            json_file = root / "session.json"
            dotenv_file = root / ".env"
            markdown.write_bytes(b"before " + secret + b" after " + secret)
            json_file.write_bytes(b'{"value":"' + secret + b'"}')
            dotenv_file.write_bytes(b"KEY=" + secret)

            report = redact_text_files.redact_tree(root, secret, apply=False)

            self.assertEqual(report.replacement_count, 4)
            self.assertEqual(
                report.matched_files,
                (dotenv_file, json_file, markdown),
            )
            self.assertEqual(report.skipped_files, ())
            self.assertIn(secret, markdown.read_bytes())
            self.assertIn(secret, json_file.read_bytes())
            self.assertIn(secret, dotenv_file.read_bytes())

    def test_apply_replaces_literal_secret_and_preserves_mode(self) -> None:
        secret = b"[literal]/secret.*"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "config.yaml"
            target.write_bytes(b"key: " + secret + b"\n")
            target.chmod(0o640)

            report = redact_text_files.redact_tree(root, secret, apply=True)

            self.assertEqual(report.replacement_count, 1)
            self.assertEqual(
                target.read_bytes(),
                b"key: ***REDACTED***\n",
            )
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o640)

    def test_skips_non_utf8_and_oversized_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            binary_text = root / "binary.log"
            oversized = root / "large.txt"
            binary_text.write_bytes(b"\xffx")
            oversized.write_text("secret", encoding="utf-8")

            report = redact_text_files.redact_tree(
                root,
                b"secret",
                apply=True,
                max_bytes=5,
            )

            self.assertEqual(report.replacement_count, 0)
            self.assertEqual(len(report.skipped_files), 2)
            self.assertEqual(
                {skipped.reason for skipped in report.skipped_files},
                {"file is not UTF-8 text", "file exceeds 5 bytes"},
            )
            self.assertEqual(binary_text.read_bytes(), b"\xffx")
            self.assertEqual(oversized.read_text(encoding="utf-8"), "secret")

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links unavailable")
    def test_reports_symbolic_links_without_following_them(self) -> None:
        secret = b"outside-secret"
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            root = workspace / "scan"
            root.mkdir()
            outside = workspace / "outside.md"
            outside.write_bytes(secret)
            link = root / "linked.md"
            link.symlink_to(outside)

            report = redact_text_files.redact_tree(root, secret, apply=True)

            self.assertEqual(report.replacement_count, 0)
            self.assertEqual(
                report.skipped_files,
                (redact_text_files.SkippedFile(link, "symbolic link"),),
            )
            self.assertEqual(outside.read_bytes(), secret)

    def test_rejects_empty_secret(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary_directory,
            self.assertRaisesRegex(ValueError, "cannot be empty"),
        ):
            redact_text_files.redact_tree(
                Path(temporary_directory),
                b"",
                apply=False,
            )


if __name__ == "__main__":
    unittest.main()

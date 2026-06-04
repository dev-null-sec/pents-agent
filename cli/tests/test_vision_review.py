from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from pents.cli import main


PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000a49444154789c63600000020001e221bc3300000000"
    "49454e44ae426082"
)


class VisionReviewTests(unittest.TestCase):
    def test_mock_review_writes_structured_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "page.png"
            out = Path(tmp) / "review.json"
            image.write_bytes(PNG_1X1)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(
                    [
                        "vision-review",
                        str(image),
                        "--question",
                        "判断页面是否有验证码",
                        "--mock",
                        "--out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "ok")
            self.assertEqual(data["mode"], "mock")
            self.assertEqual(data["image"]["mime_type"], "image/png")
            self.assertEqual(data["result"]["blocker"], "mock_mode_no_image_read")
            self.assertIn('"mock_mode_no_image_read"', stdout.getvalue())

    def test_missing_api_key_returns_error_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "page.png"
            image.write_bytes(PNG_1X1)

            stdout = io.StringIO()
            with patch.dict(os.environ, {"PENTS_VISION_API_KEY": ""}, clear=False):
                with redirect_stdout(stdout):
                    code = main(
                        [
                            "vision-review",
                            str(image),
                            "--question",
                            "判断页面是否有验证码",
                            "--model",
                            "vision-model",
                        ]
                    )

            self.assertEqual(code, 2)
            data = json.loads(stdout.getvalue())
            self.assertEqual(data["status"], "error")
            self.assertEqual(data["error_type"], "missing_api_key")
            self.assertNotIn("sk-", stdout.getvalue().lower())

    def test_env_file_supplies_vision_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "page.png"
            image.write_bytes(PNG_1X1)
            (root / ".env").write_text(
                "\n".join(
                    [
                        "PENTS_VISION_API_KEY=file-key",
                        "PENTS_VISION_BASE_URL=https://vision.example.test/v1",
                        "PENTS_VISION_MODEL=file-model",
                    ]
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with patch("pents.cli.workspace_root", return_value=root):
                with patch.dict(os.environ, {}, clear=True):
                    with redirect_stdout(stdout):
                        code = main(
                            [
                                "vision-review",
                                str(image),
                                "--question",
                                "判断页面是否有验证码",
                                "--mock",
                            ]
                        )

            self.assertEqual(code, 0)
            data = json.loads(stdout.getvalue())
            self.assertEqual(data["model"], "file-model")
            self.assertEqual(data["api_base_url"], "https://vision.example.test/v1")
            self.assertEqual(data["env_files_loaded"], [str(root / ".env")])


if __name__ == "__main__":
    unittest.main()

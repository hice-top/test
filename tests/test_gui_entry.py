from __future__ import annotations

import unittest


class GuiEntryTests(unittest.TestCase):
    def test_module_imports(self) -> None:
        import app.gui as gui  # noqa: PLC0415

        self.assertTrue(callable(gui.main))


if __name__ == "__main__":
    unittest.main()

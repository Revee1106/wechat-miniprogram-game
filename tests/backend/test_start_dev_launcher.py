from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CMD_PATH = ROOT / "start-dev.cmd"
PS1_PATH = ROOT / "start-dev.ps1"


class StartDevLauncherTests(unittest.TestCase):
    def test_cmd_launcher_invokes_powershell_script(self):
        source = CMD_PATH.read_text(encoding="utf-8")

        self.assertIn("start-dev.ps1", source)
        self.assertIn("powershell", source.lower())

    def test_powershell_launcher_targets_expected_projects_and_backend_command(self):
        source = PS1_PATH.read_text(encoding="utf-8")

        self.assertIn("wechat-miniprogram-game-front", source)
        self.assertIn("PYTHONPATH", source)
        self.assertIn("uvicorn", source)
        self.assertIn("app.main:app", source)
        self.assertIn("127.0.0.1", source)
        self.assertIn("8000", source)

    def test_powershell_launcher_guides_frontend_manual_steps(self):
        source = PS1_PATH.read_text(encoding="utf-8")

        self.assertIn("WeChat DevTools", source)
        self.assertIn("api/health", source)

    def test_powershell_launcher_validates_venv_and_has_local_python_fallback(self):
        source = PS1_PATH.read_text(encoding="utf-8")

        self.assertIn("Test-PythonLauncher", source)
        self.assertIn("pythoncore-3.14-64", source)
        self.assertIn("--version", source)


if __name__ == "__main__":
    unittest.main()

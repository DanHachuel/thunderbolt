import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class NpxCacheCompatibilityTests(unittest.TestCase):
    def test_package_runs_cache_compatibility_postinstall(self):
        manifest = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(
            manifest["scripts"]["postinstall"],
            "node scripts/npx-cache-compat.mjs",
        )

    def test_compatibility_script_only_writes_inside_npx_cache(self):
        source = (ROOT / "scripts" / "npx-cache-compat.mjs").read_text(encoding="utf-8")
        self.assertIn('pathParts.includes("_npx")', source)
        self.assertIn('resolve(npxCacheRoot, "package.json")', source)
        self.assertIn('writeFileSync(packageJsonPath', source)

    def test_runtime_subprocesses_receive_persistent_storage_environment(self):
        source = (ROOT / "scripts" / "cli.mjs").read_text(encoding="utf-8")
        self.assertIn('THUNDERBOLT_STORAGE_DIR: storageDir', source)
        self.assertIn('"worker de automação", runtimeEnv', source)
        self.assertIn('"worker do pipeline de vídeos", runtimeEnv', source)

    def test_install_recovers_ai_influencer_database_from_previous_npx_cache(self):
        source = (ROOT / "scripts" / "install.mjs").read_text(encoding="utf-8")
        self.assertIn('function migrateLegacyNpxStorage()', source)
        self.assertIn('ai_influencers.db', source)
        self.assertIn('copyMissingTree(join(candidate, "storage"), targetStorage)', source)
        self.assertIn('migrateLegacyNpxStorage();', source)

    def test_install_persists_dependency_hash_inside_venv_and_checks_growth_dependencies(self):
        source = (ROOT / "scripts" / "install.mjs").read_text(encoding="utf-8")
        self.assertIn('const markerPath = join(venvPath, `.${stateKey}.sha256`);', source)
        self.assertIn('const persistedHashMatches = hashMatches || markerHash === currentHash;', source)
        self.assertIn('"yt_dlp"', source)
        self.assertIn('"youtube_transcript_api"', source)

    def test_npx_storage_migration_is_one_time(self):
        source = (ROOT / "scripts" / "install.mjs").read_text(encoding="utf-8")
        self.assertIn('npx-storage-migration-v1.json', source)
        self.assertIn('if (existsSync(migrationMarker)) return;', source)

    def test_required_commands_remain_documented_without_extra_flags(self):
        source = (ROOT / "scripts" / "cli.mjs").read_text(encoding="utf-8")
        self.assertIn('args[0] === "install"', source)
        self.assertIn('args[0] === "worker"', source)
        self.assertIn('"3030"', source)

    def test_streamlit_uses_preimport_encoding_bootstrap(self):
        source = (ROOT / "scripts" / "cli.mjs").read_text(encoding="utf-8")
        bootstrap = (ROOT / "scripts" / "streamlit_bootstrap.py").read_text(encoding="utf-8")
        self.assertIn('const streamlitBootstrap = resolve(root, "scripts", "streamlit_bootstrap.py");', source)
        self.assertIn('[streamlitBootstrap, "run", main', source)
        self.assertIn('from streamlit.web.cli import main', bootstrap)
        self.assertLess(bootstrap.index('os.environ["PYTHONIOENCODING"]'), bootstrap.index('from streamlit.web.cli import main'))

    def test_streamlit_bootstrap_owns_sigint_without_click_shutdown(self):
        bootstrap = (ROOT / "scripts" / "streamlit_bootstrap.py").read_text(encoding="utf-8")
        self.assertIn("def _custom_sigint_handler", bootstrap)
        self.assertIn("asyncio.get_running_loop()", bootstrap)
        self.assertIn("loop.call_soon_threadsafe(loop.stop)", bootstrap)
        self.assertIn("os._exit(0)", bootstrap)
        self.assertIn("_original_signal(signal.SIGINT, _custom_sigint_handler)", bootstrap)
        self.assertIn("signal.signal = _protected_signal", bootstrap)
        self.assertNotIn("server.stop()", bootstrap)

    def test_package_manifest_includes_python_streamlit_bootstrap(self):
        manifest = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertIn("scripts/*.py", manifest["files"])


if __name__ == "__main__":
    unittest.main()

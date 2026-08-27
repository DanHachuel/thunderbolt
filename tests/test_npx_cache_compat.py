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

    def test_required_commands_remain_documented_without_extra_flags(self):
        source = (ROOT / "scripts" / "cli.mjs").read_text(encoding="utf-8")
        self.assertIn('args[0] === "install"', source)
        self.assertIn('args[0] === "worker"', source)
        self.assertIn('"3030"', source)


if __name__ == "__main__":
    unittest.main()

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

    def test_required_commands_remain_documented_without_extra_flags(self):
        source = (ROOT / "scripts" / "cli.mjs").read_text(encoding="utf-8")
        self.assertIn('args[0] === "install"', source)
        self.assertIn('args[0] === "worker"', source)
        self.assertIn('"3030"', source)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = ROOT / "seed" / "prompt_masters"
STORAGE_DIR = ROOT / "storage" / "tiktok" / "prompts_master"
STORAGE_SOURCE = (ROOT / "hermes_ui" / "storage.py").read_text(encoding="utf-8")
INSTALL_SOURCE = (ROOT / "scripts" / "install.mjs").read_text(encoding="utf-8")
PACKAGE_SOURCE = (ROOT / "package.json").read_text(encoding="utf-8")


def test_all_prompt_masters_are_bundled_as_seed_content():
    seed_files = sorted(SEED_DIR.glob("*.md"))
    storage_files = sorted(STORAGE_DIR.glob("*.md"))
    assert len(seed_files) == 50
    assert {path.name for path in seed_files} <= {path.name for path in storage_files}
    assert len(storage_files) >= len(seed_files)
    assert all(path.read_text(encoding="utf-8").strip() for path in seed_files)


def test_python_storage_seeds_without_overwriting_existing_files():
    assert 'SEED_TIKTOK_PROMPT_MASTERS = ROOT / "seed" / "prompt_masters"' in STORAGE_SOURCE
    assert 'def seed_prompt_masters()' in STORAGE_SOURCE
    assert 'seed_prompt_masters()' in STORAGE_SOURCE
    assert 'if not target.exists():' in STORAGE_SOURCE
    assert 'shutil.copy2(source, target)' in STORAGE_SOURCE


def test_npx_installer_seeds_prompt_masters_without_overwriting_existing_files():
    assert 'join(storageRoot, "tiktok", "prompts_master")' in INSTALL_SOURCE
    assert 'function copySeedPromptMasters(storageRoot)' in INSTALL_SOURCE
    assert 'join(root, "seed", "prompt_masters")' in INSTALL_SOURCE
    assert 'if (!existsSync(target)) copyFileSync(source, target);' in INSTALL_SOURCE
    assert 'seed/prompt_masters/**/*.md' in PACKAGE_SOURCE


def test_seed_prompt_masters_are_listed_alphabetically():
    names = [path.name for path in sorted(SEED_DIR.glob("*.md"), key=lambda path: (path.name.casefold(), path.name))]
    assert names == sorted(names, key=lambda name: (name.casefold(), name))
    assert names[0] == "2Dstickman.md"
    assert names[-1] == "VisualCraftSequenceGenerator.md"
    assert 'key=lambda p: (p.name.casefold(), p.name)' in STORAGE_SOURCE
    assert 'st_mtime' not in STORAGE_SOURCE.split('def list_prompt_master_files', 1)[1].split('def load_prompt_master_file', 1)[0]

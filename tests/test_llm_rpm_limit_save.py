from pathlib import Path


def test_nvidia_nim_limit_has_dedicated_save_and_persisted_values():
    source = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")
    block_start = source.index('st.markdown("### Limite LLM NVIDIA NIM")')
    block_end = source.index('for index in range(len(cards)):', block_start)
    block = source[block_start:block_end]
    assert 'key="save_llm_rpm_limit"' in block
    assert '"llm_rpm_limit_enabled": bool(llm_rpm_limit_enabled)' in block
    assert '"llm_rpm_limit": int(llm_rpm_limit)' in block
    assert '"llm_rpm_window_seconds": int(llm_rpm_window_seconds)' in block
    assert 'write_json("settings.json", settings)' in block

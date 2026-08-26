from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hermes_ui import provider_routing


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text
        self.headers: dict[str, str] = {}

    def json(self):
        return self._payload


class ProviderRoutingTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.storage_root = Path(self.tempdir.name)
        self.state = self.storage_root / "state"
        self.state.mkdir(parents=True)
        self.storage_patch = patch.object(provider_routing, "STORAGE", self.storage_root)
        self.storage_patch.start()
        self.ensure_patch = patch.object(provider_routing, "ensure_storage", lambda: None)
        self.ensure_patch.start()

    def tearDown(self):
        self.ensure_patch.stop()
        self.storage_patch.stop()
        self.tempdir.cleanup()

    def test_nvidia_rpm_disabled_does_not_reserve_slot(self):
        settings = {"llm_rpm_limit_enabled": False, "llm_rpm_limit": 40}
        card = {"id": "nim", "provider": "openai", "base_url": "https://integrate.api.nvidia.com/v1", "api_key": "secret", "model": "m"}
        waited = provider_routing.acquire_nvidia_rpm_slot(settings, card, sleep=False)
        self.assertEqual(waited, 0.0)
        self.assertFalse((self.state / provider_routing.RATE_LIMIT_FILENAME).exists())

    def test_nvidia_rpm_uses_40_slots_in_60_second_window_without_secret_in_state(self):
        settings = {"llm_rpm_limit_enabled": True, "llm_rpm_limit": 40, "llm_rpm_window_seconds": 60}
        card = {"id": "nim", "provider": "openai", "base_url": "https://integrate.api.nvidia.com/v1", "api_key": "SECRET-DONT-PERSIST", "model": "m"}
        clock = [1000.0]
        now = lambda: clock[0]
        for _ in range(40):
            self.assertEqual(provider_routing.acquire_nvidia_rpm_slot(settings, card, sleep=False, now=now), 0.0)
        wait_for = provider_routing.acquire_nvidia_rpm_slot(settings, card, sleep=False, now=now)
        self.assertEqual(wait_for, 60.0)
        raw = (self.state / provider_routing.RATE_LIMIT_FILENAME).read_text(encoding="utf-8")
        self.assertNotIn("SECRET-DONT-PERSIST", raw)
        clock[0] += 60.1
        self.assertEqual(provider_routing.acquire_nvidia_rpm_slot(settings, card, sleep=False, now=now), 0.0)

    def test_route_fails_over_on_timeout_and_returns_second_card(self):
        settings = {"provider_max_attempts": 2, "provider_cooldown_seconds": 0}
        cards = [
            {"id": "one", "provider": "openai", "base_url": "https://one.example/v1", "api_key": "one", "model": "m"},
            {"id": "two", "provider": "openai", "base_url": "https://two.example/v1", "api_key": "two", "model": "m"},
        ]
        responses = [FakeResponse(503, text="temporary"), FakeResponse(200, {"choices": [{"message": {"content": "{}"}}]})]
        used = []

        def request(card):
            used.append(card["id"])
            return responses.pop(0)

        routed = provider_routing.route_json_request(settings, pool=provider_routing.POOL_LLM, cards=cards, request=request, cooldown_seconds=0)
        self.assertEqual(routed.card["id"], "two")
        self.assertEqual(used, ["one", "two"])
        attempts = json.loads((self.state / provider_routing.ATTEMPTS_FILENAME).read_text(encoding="utf-8"))
        self.assertEqual([item["category"] for item in attempts], ["transient", "success"])
        self.assertTrue(all("api_key" not in item and "one" not in item.get("error", "") for item in attempts))

    def test_route_does_not_fail_over_for_payload_400(self):
        settings = {"provider_max_attempts": 2, "provider_cooldown_seconds": 0}
        cards = [
            {"id": "one", "provider": "openai", "base_url": "https://one.example/v1", "api_key": "one", "model": "m"},
            {"id": "two", "provider": "openai", "base_url": "https://two.example/v1", "api_key": "two", "model": "m"},
        ]
        used = []

        def request(card):
            used.append(card["id"])
            return FakeResponse(400, text="invalid request")

        with self.assertRaises(provider_routing.ProviderRoutingError):
            provider_routing.route_json_request(settings, pool=provider_routing.POOL_IMAGE, cards=cards, request=request, cooldown_seconds=0)
        self.assertEqual(used, ["one"])

    def test_route_skips_persisted_cooldown(self):
        settings = {"provider_max_attempts": 2, "provider_cooldown_seconds": 10}
        first = {"id": "one", "provider": "openai", "base_url": "https://one.example/v1", "api_key": "one", "model": "m"}
        second = {"id": "two", "provider": "openai", "base_url": "https://two.example/v1", "api_key": "two", "model": "m"}
        provider_routing.set_provider_cooldown(first, 120)
        used = []

        def request(card):
            used.append(card["id"])
            return FakeResponse(200, {"ok": True})

        routed = provider_routing.route_json_request(settings, pool=provider_routing.POOL_VIDEO, cards=[first, second], request=request, cooldown_seconds=0)
        self.assertEqual(routed.card["id"], "two")
        self.assertEqual(used, ["two"])


if __name__ == "__main__":
    unittest.main()

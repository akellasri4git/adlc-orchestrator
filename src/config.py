"""Loads settings.yaml and gate_policy.yaml into typed objects."""
import os
from dataclasses import dataclass
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    repair_loop_cap: int
    credit_headroom: dict
    gates: dict
    raw: dict

    def gate_enabled(self, stage: str) -> bool:
        return self.gates.get(stage, True)  # fail safe: gate on unless explicitly off

    def secret(self, key: str) -> str:
        """key is a settings.yaml entry holding an env var name, e.g. 'postgres_dsn_env'."""
        return os.environ.get(self.raw[key], "")

    def secret_from(self, env_name: str) -> str:
        return os.environ.get(env_name, "")


def load_settings(config_dir: Path | None = None) -> Settings:
    config_dir = config_dir or ROOT / "config"
    raw = yaml.safe_load((config_dir / "settings.yaml").read_text())
    gates = yaml.safe_load((config_dir / "gate_policy.yaml").read_text())["gates"]
    return Settings(raw["repair_loop_cap"], raw["credit_headroom"], gates, raw)

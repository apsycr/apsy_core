import yaml
from pathlib import Path
import os
import logging

from modules.security import encrypt_value

BASE_DIR = Path("/config")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def ensure_encrypted_config(env_cfg, env_path):
    logging.info("servidor iniciado")
    changed = False

    for section in ["db", "db_api"]:

        if section not in env_cfg:
            continue

        db_cfg = env_cfg[section]

        # ya encriptado
        if "password" in db_cfg:
            continue

        # plaintext
        if "password_plain" in db_cfg:

            plain = db_cfg["password_plain"]

            db_cfg["password"] = encrypt_value(plain)

            del db_cfg["password_plain"]

            changed = True

    if changed:
        with open(env_path, "w", encoding="utf-8") as f:

            yaml.safe_dump(
                env_cfg,
                f,
                allow_unicode=True,
                sort_keys=False
            )

    return env_cfg


def load_config():

    # config base
    with open(BASE_DIR / "config.yml", "r", encoding="utf-8") as f:

        base = ensure_encrypted_config(yaml.safe_load(f),BASE_DIR / "config.yml")

    env_name = base.get("env", os.getenv("ENV", "dev")).lower()

    env_path = BASE_DIR / "environment" / f"{env_name}.yml"

    # config entorno
    env_cfg = {}

    if env_path.exists():

        with open(env_path, "r", encoding="utf-8") as f:

            env_cfg = yaml.safe_load(f)

        # auto encrypt del environment
        #env_cfg = ensure_encrypted_config(env_cfg, env_path)
        # merge final
        base.update(env_cfg)

    return base
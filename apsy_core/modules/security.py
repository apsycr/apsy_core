from pathlib import Path
import base64
import hashlib
import uuid
import os

from cryptography.fernet import Fernet

def get_config_dir():

    docker_path = Path("/config")

    if docker_path.exists():

        return docker_path

    env_path = os.getenv("APSY_CONFIG")

    if env_path:

        return Path(env_path)

    return Path(__file__).resolve().parent.parent / "config"

CONFIG_DIR = get_config_dir()

INSTANCE_FILE = CONFIG_DIR / "instance.id"


def get_instance_id():

    CONFIG_DIR.mkdir(exist_ok=True)

    if INSTANCE_FILE.exists():

        return INSTANCE_FILE.read_text().strip()

    new_id = str(uuid.uuid4())

    INSTANCE_FILE.write_text(new_id)

    return new_id


def get_machine_key():

    raw = get_instance_id().encode()

    hashed = hashlib.sha256(raw).digest()

    return base64.urlsafe_b64encode(hashed)


def encrypt_value(value: str) -> str:

    key = get_machine_key()

    f = Fernet(key)

    return f.encrypt(value.encode()).decode()


def decrypt_value(enc_value: str) -> str:

    key = get_machine_key()

    f = Fernet(key)

    return f.decrypt(enc_value.encode()).decode()
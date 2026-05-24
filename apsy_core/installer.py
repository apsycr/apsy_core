import os
import subprocess
import shutil
import getpass
from pathlib import Path
import yaml

# 🔐 tu lógica existente
from modules.security import decrypt_value  # si ya la tienes
from cryptography.fernet import Fernet
import base64, hashlib, uuid


# =========================
# CONFIG
# =========================
BASE_DIR = Path(__file__).parent
SERVICE_NAME = "APSY_CORE"
APP_EXE = "ws_server_local.exe"
CONFIG_FILE = BASE_DIR / "config.yml"
TEMPLATE_FILE = BASE_DIR / "config.template.yml"


# =========================
# 🔐 ENCRYPT
# =========================
def get_machine_key():
    raw = str(uuid.getnode()).encode()
    return base64.urlsafe_b64encode(hashlib.sha256(raw).digest())


def encrypt_value(value: str) -> str:
    f = Fernet(get_machine_key())
    return f.encrypt(value.encode()).decode()


# =========================
# 📥 INPUT
# =========================
def ask_passwords():
    print("\n🔐 Configuración de base de datos\n")

    db_pass = getpass.getpass("DB local password: ")
    db_api_pass = getpass.getpass("DB API password: ")

    return db_pass, db_api_pass

def update_config(db_pass, db_api_pass=None):
    if not CONFIG_FILE.exists():
        raise Exception("No existe config.yml")

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 🔐 DB LOCAL
    config.setdefault("db", {})
    config["db"]["password_enc"] = encrypt_value(db_pass)

    # 🔐 DB API (si existe en tu config)
    if "db_api" in config and db_api_pass:
        config["db_api"]["password_enc"] = encrypt_value(db_api_pass)

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)

    print("✅ config.yml actualizado")

# =========================
# ⚙️ GENERAR CONFIG
# =========================
def generate_config(db_pass, db_api_pass):
    if not TEMPLATE_FILE.exists():
        raise Exception("No existe config.template.yml")

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    config.setdefault("db", {})
    config.setdefault("db_api", {})

    config["db"]["password_enc"] = encrypt_value(db_pass)
    config["db_api"]["password_enc"] = encrypt_value(db_api_pass)

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)

    print("✅ config.yml generado")


# =========================
# 🔧 SERVICIO (NSSM)
# =========================
def install_service():
    nssm_path = BASE_DIR / "nssm.exe"

    if not nssm_path.exists():
        raise Exception("nssm.exe no encontrado")

    exe_path = str(BASE_DIR / APP_EXE)

    print("⚙️ Registrando servicio...")

    subprocess.run([str(nssm_path), "install", SERVICE_NAME, exe_path], check=True)
    subprocess.run([str(nssm_path), "set", SERVICE_NAME, "Start", "SERVICE_AUTO_START"], check=True)

    print("✅ Servicio registrado")


def start_service():
    print("🚀 Iniciando servicio...")
    subprocess.run(["net", "start", SERVICE_NAME])


# =========================
# 🚀 MAIN
# =========================
def main():
    print("===============================")
    print("  INSTALADOR APSY WS CLIENT")
    print("===============================")

    if not (BASE_DIR / APP_EXE).exists():
        print("❌ No se encuentra el ejecutable")
        return

    try:
        db_pass, db_api_pass = ask_passwords()
        generate_config(db_pass, db_api_pass)
        #install_service()
        #start_service()

        print("\n🎉 Instalación completa")

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
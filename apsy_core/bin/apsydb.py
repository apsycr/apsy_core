import os
import sys
import json
import argparse
import subprocess
import re
import shutil
import json

from pathlib import Path
from datetime import datetime

# =====================================
# CONFIG
# =====================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# CONFIG_FILE = os.path.join(
#     BASE_DIR,
#     "apsydb.json"
# )

CONFIG_FILE = Path(__file__).parent / "apsydb.json"

# =====================================
# LOAD CONFIG
# =====================================

DEFAULT_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "container": "apsy_mariadb",
    "backup_dir": "C:/apsy_data/backups"
}

if os.path.exists(CONFIG_FILE):

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:

        CONFIG = json.load(f)

else:

    CONFIG = DEFAULT_CONFIG

# =====================================
# ARGS
# =====================================

parser = argparse.ArgumentParser()

parser.add_argument(
    "action",
    choices=["backup", "restore", "shell", "clean"]
)

parser.add_argument(
    "file",
    nargs="?"
)

parser.add_argument(
    "-d",
    "--database",
    default="production"
)

parser.add_argument(
    "-p",
    "--password",
    default="Login2Help"
)

parser.add_argument(
    "-u",
    "--user",
    default="itech01"
)

parser.add_argument(
    "-P",
    "--port",
    type=int,
    default=CONFIG.get("port", 3306)
)

parser.add_argument(
    "-hst",
    "--host",
    default=CONFIG.get("host", "localhost")
)

parser.add_argument(
    "-l",
    "--location",
    choices=["docker", "legacy"],
    default="docker"
)

parser.add_argument(
    "--no-display",
    action="store_true"
)

args = parser.parse_args()

# =====================================
# CODIGOS
# =====================================

PROCESS_COMPLETE = 0
RESTORE_ERROR    = 1

# =====================================
# VARIABLES
# =====================================

MYSQL_USER      = args.user

MYSQL_PASSWORD  = args.password

MYSQL_DATABASE  = args.database

MYSQL_PORT      = args.port

MYSQL_HOST      = args.host

MODE            = args.location

NO_DISPLAY      = args.no_display

CONTAINER = CONFIG.get(
    "container",
    "apsy_mariadb"
)

BACKUP_DIR = CONFIG.get(
    "backup_dir",
    "C:/ProgramData/apsy/backups"
)

os.makedirs(
    BACKUP_DIR,
    exist_ok=True
)

# =====================================
# RUN
# =====================================

def run(cmd):

    print("\n>>", " ".join(cmd), "\n")

    result = subprocess.run(cmd)

    if result.returncode != 0:

        sys.exit(result.returncode)

# =====================================
# CLEAN SQL
# =====================================

def clean_sql_file(file_path):


    fecha = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_file = f"{file_path}.{fecha}.bak"

    shutil.copy2(
        file_path,
        backup_file
    )

    if not NO_DISPLAY:
         print(f"\n{'🛡' if not NO_DISPLAY else ''} Backup original:\n{backup_file}")

         print(f"\n{'🧹' if not NO_DISPLAY else ''} Limpiando dump...\n")

    # with open(file_path, "r", encoding="utf-8") as f:

    #     sql = f.read()

    encodings = ['utf-8', 'cp1252', 'latin1']

    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                sql = f.read()
            print(f"Codificación detectada: {enc}")
            break
        except UnicodeDecodeError:
            pass
    else:
        raise Exception("No se pudo determinar la codificación")

    # =================================
    # HEADER UTF8MB4
    # =================================

    header = """
SET NAMES utf8mb4;
SET collation_connection = 'utf8mb4_unicode_ci';

"""

    sql = header + sql

    # =================================
    # REMOVE DEFINERS
    # =================================

    sql = re.sub(
        r"DEFINER=`[^`]+`@`[^`]+`",
        "",
        sql
    )

    replacements = {

        "utf8mb3_general_ci": "utf8mb4_unicode_ci",

        "utf8_general_ci": "utf8mb4_unicode_ci",

        "utf8mb4_general_ci": "utf8mb4_unicode_ci",

        "CHARSET=utf8mb3;": "CHARSET=utf8mb4;",

        "CHARSET=utf8;": "CHARSET=utf8mb4;",

        "CHARSET=utf8mb3 ": "CHARSET=utf8mb4 ",

        "CHARSET=utf8 ": "CHARSET=utf8mb4 ",

        "CHARACTER SET utf8mb3;": "CHARACTER SET utf8mb4;",

        "CHARACTER SET utf8;": "CHARACTER SET utf8mb4;",

        "CHARACTER SET utf8mb3 ": "CHARACTER SET utf8mb4 ",

        "CHARACTER SET utf8 ": "CHARACTER SET utf8mb4 ",

        "SET NAMES utf8;": "SET NAMES utf8mb4;",

        "SET NAMES utf8 ": "SET NAMES utf8mb4 ",

        "character_set_client  = utf8 ": "character_set_client  = utf8mb4 ",

        "character_set_results = utf8 ": "character_set_results = utf8mb4 ",

        "character_set_client = utf8 ": "character_set_client = utf8mb4 ",

        "character_set_results = utf8 ": "character_set_results = utf8mb4 ",

        "character_set_client  = utf8;": "character_set_client  = utf8mb4;",

        "character_set_results = utf8;": "character_set_results = utf8mb4;",

        "character_set_client = utf8;": "character_set_client = utf8mb4;",

        "character_set_results = utf8;": "character_set_results = utf8mb4;",
    }

    for old, new in replacements.items():

        sql = sql.replace(old, new)

    sql = re.sub(
        r"DEFAULT CHARSET=utf8mb4(?!\s+COLLATE=)",
        "DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci",
        sql
    )

    # =================================
    # SAVE
    # =================================

    with open(file_path, "w", encoding="utf-8") as f:

        f.write(sql)

    print(f"\n{'✅' if not NO_DISPLAY else ''} Dump limpio y convertido a utf8mb4_unicode_ci")

# =====================================
# BACKUP
# =====================================

def backup():

    fecha = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    file = os.path.join(
        BACKUP_DIR,
        f"{MYSQL_DATABASE}_{fecha}.sql"
    )

    # =================================
    # DOCKER
    # =================================

    if MODE == "docker":

        cmd = [
            "docker",
            "exec",
            CONTAINER,

            "mariadb-dump",

            "--default-character-set=utf8mb4",

            "--skip-set-charset",

            "--single-transaction",

            "--routines",
            "--events",
            "--triggers",

            "--skip-comments",

            "-u", MYSQL_USER,
            f"-p{MYSQL_PASSWORD}",

            MYSQL_DATABASE
        ]

    # =================================
    # LEGACY
    # =================================

    else:

        cmd = [
            "mysqldump",

            "--default-character-set=utf8mb4",

            "--skip-set-charset",

            "--single-transaction",

            "--routines",
            "--events",
            "--triggers",

            "--skip-comments",

            "-h", MYSQL_HOST,
            "-P", str(MYSQL_PORT),

            "-u", MYSQL_USER,
            f"-p{MYSQL_PASSWORD}",

            MYSQL_DATABASE
        ]

    # =================================
    # CREATE DUMP
    # =================================

    with open(file, "w", encoding="utf-8") as f:

        result = subprocess.run(
            cmd,
            stdout=f
        )

    if result.returncode != 0:
        print(f"\n{'❌' if not NO_DISPLAY else ''} Error creando backup")

        return

    # =================================
    # CLEAN SQL
    # =================================

    clean_sql_file(file)
    
    print(f"\n{'✅' if not NO_DISPLAY else ''} Backup creado:\n{file}")

# =====================================
# CLEAN
# =====================================

def clean(file):

    if not file:
        print(f"\n{'❌' if not NO_DISPLAY else ''} Debe indicar archivo")

        return

    if not os.path.exists(file):
        print(f"\n{'❌' if not NO_DISPLAY else ''} Archivo no existe")

        return

    clean_sql_file(file)

    print(f"\n{'✅' if not NO_DISPLAY else ''} Archivo limpiado")

# =====================================
# RESTORE
# =====================================

def restore(file):

    if not file:

        print(f"\n{'❌' if not NO_DISPLAY else ''} Debe indicar archivo")

        return

    if not os.path.exists(file):

        print(f"\n{'❌' if not NO_DISPLAY else ''} Archivo no existe")

        return

    # =================================
    # DOCKER
    # =================================

    if MODE == "docker":

        cmd = [
            "docker",
            "exec",
            "-i",
            CONTAINER,

            "mariadb",

            "--default-character-set=utf8mb4",

            "-u", MYSQL_USER,
            f"-p{MYSQL_PASSWORD}",
            "-A",
            MYSQL_DATABASE
        ]

    # =================================
    # LEGACY
    # =================================

    else:

        cmd = [
            "mysql",

            "--default-character-set=utf8mb4",

            "-h", MYSQL_HOST,
            "-P", str(MYSQL_PORT),

            "-u", MYSQL_USER,
            f"-p{MYSQL_PASSWORD}",

            MYSQL_DATABASE
        ]

    # =================================
    # RESTORE
    # =================================

    with open(file, "rb") as f:

        result = subprocess.run(
            cmd,
            stdin=f
        )

    if result.returncode == 0:

        if not NO_DISPLAY: 
            print("\n✅ Restore completado")
        
        return PROCESS_COMPLETE

    else:
        if not NO_DISPLAY:
            print("\n❌ Error en restore")
        
        return RESTORE_ERROR 

# =====================================
# SHELL
# =====================================

def shell():

    # =================================
    # DOCKER
    # =================================

    if MODE == "docker":

        cmd = [
            "docker",
            "exec",
            "-it",
            CONTAINER,

            "mariadb",

            "--default-character-set=utf8mb4",

            "-u", MYSQL_USER,
            f"-p{MYSQL_PASSWORD}",
            f"{MYSQL_DATABASE}",
            "-A"
        ]

    # =================================
    # LEGACY
    # =================================

    else:

        cmd = [
            "mariadb",

            "--default-character-set=utf8mb4",

            "-h", MYSQL_HOST,
            "-P", str(MYSQL_PORT),

            "-u", MYSQL_USER,
            f"-p{MYSQL_PASSWORD}"
        ]

    os.system(" ".join(cmd))

# =====================================
# MAIN
# =====================================

if args.action == "backup":

    backup()

elif args.action == "restore":

    restore(args.file)

elif args.action == "shell":

    shell()

elif args.action == "clean":

    clean(args.file)
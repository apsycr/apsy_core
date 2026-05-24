import sys
from modules.security import encrypt_value


def main():

    if len(sys.argv) < 2:

        print("Uso: py encriptar.py [CONTRASEÑA]")

        return

    password = sys.argv[1]

    encrypted = encrypt_value(password)

    print("\n🔐 Password encriptado:\n")

    print(encrypted)

    print("\n📌 Copiar en config.yml como:\n")

    print(f"password: {encrypted}\n")


if __name__ == "__main__":

    main()
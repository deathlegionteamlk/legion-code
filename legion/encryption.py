import os
import hashlib
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


class Encryptor:
    def __init__(self, key: bytes = None):
        self.key = key

    def generate_key(self) -> bytes:
        self.key = get_random_bytes(32)
        return self.key

    def key_from_passphrase(self, passphrase: str, salt: bytes = None) -> bytes:
        if salt is None:
            salt = get_random_bytes(16)
        self.key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 100000, dklen=32)
        return self.key

    def encrypt_file(self, input_path: str, output_path: str = None) -> str:
        if self.key is None:
            raise ValueError("Encryption key not set. Call generate_key() or key_from_passphrase() first.")
        if output_path is None:
            output_path = input_path + ".enc"
        iv = get_random_bytes(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        with open(input_path, "rb") as f:
            plaintext = f.read()
        ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
        with open(output_path, "wb") as f:
            f.write(iv + ciphertext)
        return output_path

    def decrypt_file(self, input_path: str, output_path: str = None) -> str:
        if self.key is None:
            raise ValueError("Encryption key not set. Call generate_key() or key_from_passphrase() first.")
        if output_path is None:
            output_path = input_path.replace(".enc", ".dec") if input_path.endswith(".enc") else input_path + ".dec"
        with open(input_path, "rb") as f:
            data = f.read()
        iv = data[:AES.block_size]
        ciphertext = data[AES.block_size:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
        with open(output_path, "wb") as f:
            f.write(plaintext)
        return output_path

    def encrypt_bytes(self, data: bytes) -> bytes:
        if self.key is None:
            raise ValueError("Encryption key not set.")
        iv = get_random_bytes(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(pad(data, AES.block_size))

    def decrypt_bytes(self, data: bytes) -> bytes:
        if self.key is None:
            raise ValueError("Encryption key not set.")
        iv = data[:AES.block_size]
        ciphertext = data[AES.block_size:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ciphertext), AES.block_size)
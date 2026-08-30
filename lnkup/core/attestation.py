from __future__ import annotations

import base64
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .integrity import sha256_file, verify_integrity


def generate_signing_key(private_path: str | Path, public_path: str | Path | None = None) -> tuple[Path, Path]:
    private_path = Path(private_path).expanduser()
    public_path = Path(public_path).expanduser() if public_path else private_path.with_suffix(".pub.pem")
    private_path.parent.mkdir(parents=True, exist_ok=True)
    key = Ed25519PrivateKey.generate()
    private_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    public_path.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    return private_path.resolve(), public_path.resolve()


def attest_run(run_directory: str | Path, private_key_path: str | Path) -> Path:
    root = Path(run_directory)
    ok, status = verify_integrity(root)
    if not ok:
        raise ValueError(f"Evidence integrity verification failed: {status}")
    key = serialization.load_pem_private_key(Path(private_key_path).read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("Signing key must be an Ed25519 private key")
    integrity_bytes = (root / "integrity.json").read_bytes()
    signature = key.sign(integrity_bytes)
    public_pem = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    payload = {
        "schema": 1,
        "algorithm": "Ed25519",
        "signed_at": datetime.now(timezone.utc).isoformat(),
        "signed_object": "integrity.json",
        "signed_object_sha256": sha256_file(root / "integrity.json"),
        "public_key_pem": public_pem,
        "signature_base64": base64.b64encode(signature).decode(),
    }
    path = root / "attestation.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def verify_attestation(run_directory: str | Path) -> tuple[bool, str]:
    root = Path(run_directory)
    path = root / "attestation.json"
    if not path.is_file():
        return False, "attestation.json missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        integrity = root / payload["signed_object"]
        if sha256_file(integrity) != payload["signed_object_sha256"]:
            return False, "signed object hash mismatch"
        public = serialization.load_pem_public_key(payload["public_key_pem"].encode())
        if not isinstance(public, Ed25519PublicKey):
            return False, "unsupported public key"
        public.verify(base64.b64decode(payload["signature_base64"]), integrity.read_bytes())
        return True, "verified"
    except Exception as exc:
        return False, str(exc)


def export_attested_bundle(run_directory: str | Path, private_key_path: str | Path, destination: str | Path) -> Path:
    root = Path(run_directory)
    attest_run(root, private_key_path)
    destination = Path(destination).expanduser()
    if destination.suffix.lower() != ".zip":
        destination = destination.with_suffix(".zip")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ("manifest.json", "events.jsonl", "integrity.json", "attestation.json"):
            source = root / name
            if source.is_file():
                archive.write(source, arcname=f"{root.name}/{name}")
    return destination.resolve()

from __future__ import annotations

import argparse
from lnkup.core.attestation import generate_signing_key, verify_attestation


def main() -> int:
    parser = argparse.ArgumentParser(description="LNK-NG evidence attestation utilities")
    sub = parser.add_subparsers(dest="command", required=True)
    keygen = sub.add_parser("keygen")
    keygen.add_argument("private_key")
    verify = sub.add_parser("verify")
    verify.add_argument("run_directory")
    args = parser.parse_args()
    if args.command == "keygen":
        private, public = generate_signing_key(args.private_key)
        print(f"Private key: {private}\nPublic key: {public}")
        return 0
    ok, detail = verify_attestation(args.run_directory)
    print(f"{'VERIFIED' if ok else 'FAILED'}: {detail}")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())

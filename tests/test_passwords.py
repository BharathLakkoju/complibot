from complibot.auth.passwords import hash_password, verify_password


def test_verify_rejects_low_iteration_hashes() -> None:
    stored = "pbkdf2_sha256$100000$abc$" + "0" * 64
    assert verify_password("x", stored) is False


def test_hash_and_verify_roundtrip() -> None:
    h = hash_password("securepass1")
    assert verify_password("securepass1", h)
    assert not verify_password("wrong", h)

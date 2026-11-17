import random

from PIL import Image

from stegano_config import DELIMITER, LEGACY_DUAL_HEADER, LEGACY_HEADER, STEALTH_HEADER
from stegano_core import (
    decode_dual_image,
    decode_image,
    encode_dual_image,
    encode_image,
)


def _make_virgin_cover(path, size=(128, 128)):
    Image.new("RGB", size, color=(10, 20, 30)).save(path)


def test_repeated_single_layer_recoding_preserves_virgin_cover(tmp_path):
    cover = tmp_path / "virgin.png"
    output = tmp_path / "reencoded.png"
    _make_virgin_cover(cover)
    original_cover = cover.read_bytes()

    rng = random.Random(20261114)
    alphabet = "abcXYZ0123 é🙂"
    lengths = (1, 15, 16, 17, 31, 32, 33, 255, 1024)
    passwords = ("", "short", "different password", "pässword🔒")

    for index in range(64):
        length = lengths[index % len(lengths)]
        message = "".join(rng.choice(alphabet) for _ in range(length))
        password = passwords[index % len(passwords)]
        header = STEALTH_HEADER if index % 2 == 0 else LEGACY_HEADER

        encode_image(
            str(cover),
            message,
            str(output),
            header,
            DELIMITER,
            password=password,
        )

        decoded, was_encrypted = decode_image(
            str(output),
            DELIMITER,
            password=password,
        )

        assert decoded == message, f"round-trip failed at iteration {index}"
        assert was_encrypted is bool(password)
        assert cover.read_bytes() == original_cover


def test_repeated_dual_layer_recoding_covers_password_combinations(tmp_path):
    cover = tmp_path / "virgin.png"
    output = tmp_path / "reencoded_dual.png"
    _make_virgin_cover(cover)
    original_cover = cover.read_bytes()

    password_pairs = (
        ("", ""),
        ("alpha", "beta"),
        ("same", "same"),
        ("alpha", ""),
        ("", "beta"),
    )

    for index in range(64):
        pass1, pass2 = password_pairs[index % len(password_pairs)]
        message1 = f"layer one {index}: café 🐢"
        message2 = f"layer two {index}: Δοκιμή"

        encode_dual_image(
            str(cover),
            message1,
            message2,
            str(output),
            LEGACY_DUAL_HEADER,
            DELIMITER,
            pass1=pass1,
            pass2=pass2,
        )

        decoded2, layer_count, was_encrypted, decoded1 = decode_dual_image(
            str(output),
            DELIMITER,
            pass1=pass1,
            pass2=pass2,
        )

        assert layer_count == 2, f"dual-layer decode failed at iteration {index}"
        assert decoded1 == message1, f"layer 1 mismatch at iteration {index}"
        assert decoded2 == message2, f"layer 2 mismatch at iteration {index}"
        assert was_encrypted is bool(pass2 or pass1)
        assert cover.read_bytes() == original_cover


def test_dual_layer_wrong_and_missing_password_cases(tmp_path):
    cover = tmp_path / "virgin.png"
    output = tmp_path / "dual.png"
    _make_virgin_cover(cover)

    encode_dual_image(
        str(cover),
        "first layer",
        "second layer",
        str(output),
        LEGACY_DUAL_HEADER,
        DELIMITER,
        pass1="first-key",
        pass2="second-key",
    )

    layer2, count, encrypted, layer1 = decode_dual_image(
        str(output), DELIMITER, pass1="first-key", pass2=""
    )
    assert (layer2, count, encrypted, layer1) == (
        "first layer",
        1,
        True,
        "first layer",
    )

    assert decode_dual_image(
        str(output), DELIMITER, pass1="wrong-key", pass2="second-key"
    ) == ("", 0, False, "")

    try:
        decode_dual_image(
            str(output), DELIMITER, pass1="first-key", pass2="wrong-key"
        )
    except ValueError as error:
        assert str(error) == "Incorrect password."
    else:
        raise AssertionError("an incorrect layer 2 password should fail")


def test_message_over_capacity_does_not_replace_existing_output(tmp_path):
    cover = tmp_path / "small_virgin.png"
    output = tmp_path / "existing.png"
    _make_virgin_cover(cover, size=(8, 8))
    output.write_bytes(b"existing output must remain untouched")

    try:
        encode_image(
            str(cover),
            "x" * 100,
            str(output),
            LEGACY_HEADER,
            DELIMITER,
        )
    except ValueError as error:
        assert str(error) == "Message exceeds image capacity."
    else:
        raise AssertionError("oversized message should fail")

    assert output.read_bytes() == b"existing output must remain untouched"

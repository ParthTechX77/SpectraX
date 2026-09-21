from pathlib import Path

import pytest

from app.storage.local import LocalStorage


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorage:
    return LocalStorage(tmp_path / "storage")


def test_save_and_read_bytes(storage: LocalStorage):
    data = b"SpectraX test evidence"

    relative_path = storage.save_bytes(
        data,
        "uploads",
        "sample.txt",
    )

    assert relative_path.startswith("uploads/")
    assert storage.exists(relative_path)
    assert storage.read_bytes(relative_path) == data


def test_delete_file(storage: LocalStorage):
    relative_path = storage.save_bytes(
        b"temporary data",
        "temporary",
        "temp.bin",
    )

    assert storage.exists(relative_path)

    storage.delete(relative_path)

    assert not storage.exists(relative_path)


def test_invalid_storage_category(storage: LocalStorage):
    with pytest.raises(
        ValueError,
        match="Unsupported storage category",
    ):
        storage.save_bytes(
            b"invalid",
            "invalid_category",
            "file.txt",
        )


def test_path_traversal_is_blocked(storage: LocalStorage):
    with pytest.raises(
        ValueError,
        match="Invalid storage path",
    ):
        storage.read_bytes("../../outside.txt")


def test_all_storage_directories_exist(storage: LocalStorage):
    expected_directories = {
        "uploads",
        "extracted",
        "evidence",
        "reports",
        "temporary",
    }

    assert set(storage.directories.keys()) == expected_directories

    for directory in storage.directories.values():
        assert directory.is_dir()
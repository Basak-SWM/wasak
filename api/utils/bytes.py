from typing import List


def concat(paths: List[str]) -> bytes:
    read_bytes = []

    for path in paths:
        with open(path, "rb") as f:
            read_bytes.append(f.read())

    return b"".join(read_bytes)


if __name__ == "__main__":
    result = concat(
        ["./compressed/1.webm", "./compressed/2.webm", "./compressed/3.webm"]
    )

    with open("./compressed/merged.webm", "wb") as f:
        f.write(result)

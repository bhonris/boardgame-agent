"""Generate mock board game images for testing the realtime vision pipeline."""

import io
import struct
import zlib


def create_png(width: int, height: int, color: tuple[int, int, int] = (200, 150, 100)) -> bytes:
    """Create a minimal valid PNG image with a solid color."""

    def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        chunk = chunk_type + data
        return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8-bit RGB
    ihdr = make_chunk(b"IHDR", ihdr_data)

    # Build raw pixel rows (filter byte 0 + RGB pixels)
    raw_data = b""
    for _ in range(height):
        raw_data += b"\x00" + bytes(color) * width

    idat = make_chunk(b"IDAT", zlib.compress(raw_data))
    iend = make_chunk(b"IEND", b"")

    return header + ihdr + idat + iend


def create_jpeg_stub() -> bytes:
    """Create a minimal ~valid JPEG header for testing upload acceptance."""
    # JPEG SOI + APP0 marker + minimal data + EOI
    return b"\xff\xd8\xff\xe0" + b"\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\xff\xd9"


def create_large_image(target_mb: float = 11.0) -> bytes:
    """Create a PNG that exceeds the upload size limit (default 10 MB)."""
    # A 2000x2000 uncompressed RGB image is ~12MB raw, but PNG compresses it.
    # Use random-ish data to prevent compression from shrinking it too much.
    width, height = 2000, 2000
    header = b"\x89PNG\r\n\x1a\n"

    def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        chunk = chunk_type + data
        return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)

    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = make_chunk(b"IHDR", ihdr_data)

    # Use varying pixel data to resist compression
    raw_data = b""
    for y in range(height):
        row = b"\x00"  # filter byte
        for x in range(width):
            r = (x * 7 + y * 13) % 256
            g = (x * 11 + y * 3) % 256
            b = (x * 5 + y * 17) % 256
            row += bytes([r, g, b])
        raw_data += row

    # Use no compression to guarantee large size
    idat = make_chunk(b"IDAT", zlib.compress(raw_data, 0))
    iend = make_chunk(b"IEND", b"")

    result = header + ihdr + idat + iend
    return result


def create_board_snapshot(game: str = "catan") -> bytes:
    """Create a simple colored PNG that simulates a board game snapshot.

    Different games get different colors for visual distinction.
    """
    colors = {
        "catan": (210, 160, 60),    # sandy/orange
        "wingspan": (100, 180, 100),  # green/nature
        "ticket_to_ride": (80, 120, 200),  # blue/rail
        "splendor": (180, 50, 50),   # red/gem
    }
    color = colors.get(game, (128, 128, 128))
    return create_png(640, 480, color)


if __name__ == "__main__":
    # Quick self-test
    png = create_png(100, 100)
    print(f"PNG size: {len(png)} bytes, starts with PNG header: {png[:4] == b'\\x89PNG'}")

    jpeg = create_jpeg_stub()
    print(f"JPEG size: {len(jpeg)} bytes, starts with SOI: {jpeg[:2] == b'\\xff\\xd8'}")

    large = create_large_image()
    print(f"Large image size: {len(large) / 1024 / 1024:.1f} MB")

    snap = create_board_snapshot("catan")
    print(f"Board snapshot: {len(snap)} bytes")

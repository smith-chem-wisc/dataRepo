"""How small a GPTMD database gets when stored compressed. Reads one file; writes nothing but a temp file it deletes."""
import gzip
import hashlib
import os
import sys
import tempfile
import time

sys.stdout.reconfigure(encoding="utf-8")
path = sys.argv[1]
data = open(path, "rb").read()
print(os.path.basename(path), f"{len(data)/1e6:.1f} MB, sha256 {hashlib.sha256(data).hexdigest()}")
try:
    import zstandard
    for level in (3, 19):
        t = time.time()
        z = zstandard.ZstdCompressor(level=level, threads=-1).compress(data)
        print(f"zstd -{level}: {len(z)/1e6:.1f} MB ({len(data)/len(z):.1f}x) in {time.time()-t:.0f} s")
except ImportError:
    print("zstandard not installed")
t = time.time()
g = gzip.compress(data, compresslevel=6)
print(f"gzip -6: {len(g)/1e6:.1f} MB ({len(data)/len(g):.1f}x) in {time.time()-t:.0f} s")

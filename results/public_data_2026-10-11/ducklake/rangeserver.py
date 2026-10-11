"""Static, read-only HTTP server with Range support (like HF/R2), logging each request."""
import http.server, os, re, sys

ROOT = sys.argv[1]
PORT = int(sys.argv[2])


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path) or not os.path.exists(path):
            return super().send_head()
        size = os.path.getsize(path)
        rng = self.headers.get("Range")
        f = open(path, "rb")
        if rng:
            m = re.match(r"bytes=(\d*)-(\d*)", rng)
            start = int(m.group(1)) if m.group(1) else size - int(m.group(2))
            end = int(m.group(2)) if (m.group(1) and m.group(2)) else size - 1
            end = min(end, size - 1)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Type", "application/octet-stream")
            self.end_headers()
            f.seek(start)
            self._remaining = end - start + 1
            return f
        self.send_response(200)
        self.send_header("Content-Length", str(size))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Type", "application/octet-stream")
        self.end_headers()
        self._remaining = size
        return f

    def copyfile(self, source, outputfile):
        n = getattr(self, "_remaining", None)
        if n is None:
            return super().copyfile(source, outputfile)
        while n > 0:
            buf = source.read(min(65536, n))
            if not buf:
                break
            outputfile.write(buf)
            n -= len(buf)

    def do_PUT(self):
        self.send_error(405)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.command, self.path) + (" Range=" + str(self.headers.get("Range")) if self.headers.get("Range") else "") + "\n")
        sys.stderr.flush()


http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()

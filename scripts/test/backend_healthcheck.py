import http.client
import os
import sys


def main() -> None:
    port = int(os.environ.get("API_SERVER_PORT", "8000"))
    try:
        conn = http.client.HTTPConnection("localhost", port, timeout=5)
        conn.request("GET", "/docs")
        response = conn.getresponse()
        if response.status == 200:
            sys.exit(0)
    except Exception:
        pass
    sys.exit(1)


if __name__ == "__main__":
    main()

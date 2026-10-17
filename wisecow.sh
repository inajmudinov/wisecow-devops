#!/usr/bin/env bash
set -eu
export PATH="/usr/games:$PATH"
cd /home/app
RSPFILE=response
rm -f "$RSPFILE"
mkfifo "$RSPFILE"
trap 'rm -f "$RSPFILE"' EXIT
for cmd in fortune cowsay nc; do command -v "$cmd" >/dev/null; done
handleRequest() {
    local line body
    IFS= read -r line || return 0
    # Consume request headers before writing the response.
    while IFS= read -r line; do
        [[ "$line" == $'\r' || -z "$line" ]] && break
    done
    body="<pre>$(cowsay "$(fortune)")</pre>"
    LC_ALL=C
    printf 'HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: %s\r\nConnection: close\r\n\r\n%s' "${#body}" "$body" > "$RSPFILE"
}
echo 'Wisdom served on port=4499'
while true; do
    cat "$RSPFILE" | nc -lN 4499 | handleRequest
    sleep 0.01
done

#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://127.0.0.1:8000}"
EMAIL="e2e-$(date +%s)@example.com"
PASS="securepass1"

echo "=== Register ==="
REG=$(curl -fsS -X POST "$API/v1/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"name\":\"E2E\"}")
echo "$REG" | head -c 200
TOKEN=$(echo "$REG" | python3 -c 'import sys,json; print(json.load(sys.stdin)["accessToken"])')
AUTH="Authorization: Bearer $TOKEN"

echo ""
echo "=== Create project ==="
PROJ=$(curl -fsS -X POST "$API/v1/projects" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"name":"E2E GDPR","frameworkCodes":["GDPR"]}')
PID=$(echo "$PROJ" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
echo "projectId=$PID"

export POLICY_TEXT='The Processor shall not engage another processor (sub-processor) without prior written authorisation. The Processor shall notify the Controller without undue delay after becoming aware of a personal data breach. Technical and organisational measures including encryption shall be implemented.'

echo ""
echo "=== Paste document (parity baseline) ==="
DOC=$(curl -fsS -X POST "$API/v1/projects/$PID/documents/paste" -H "$AUTH" -H 'Content-Type: application/json' \
  -d "$(python3 -c 'import json,os; print(json.dumps({"title":"policy","text":os.environ["POLICY_TEXT"]}))')")
DID=$(echo "$DOC" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
echo "paste documentId=$DID status=$(echo "$DOC" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')"

echo ""
echo "=== Presign upload (txt) ==="
UPLOAD_BYTES=$(python3 -c 'import os; print(len(os.environ["POLICY_TEXT"].encode()))')
PRESIGN=$(curl -fsS -X POST "$API/v1/projects/$PID/documents/presign" -H "$AUTH" -H 'Content-Type: application/json' \
  -d "{\"filename\":\"e2e-upload.txt\",\"contentType\":\"text/plain\",\"sizeBytes\":$UPLOAD_BYTES}")
UPLOAD_URL=$(echo "$PRESIGN" | python3 -c 'import sys,json; print(json.load(sys.stdin)["uploadUrl"])')
UPLOAD_DOC=$(echo "$PRESIGN" | python3 -c 'import sys,json; print(json.load(sys.stdin)["documentId"])')
export UPLOAD_DOC
echo "presign documentId=$UPLOAD_DOC"
printf '%s' "$POLICY_TEXT" | curl -fsS -X PUT "$UPLOAD_URL" \
  -H 'Content-Type: text/plain' --data-binary @-
COMPLETE=$(curl -fsS -X POST "$API/v1/documents/$UPLOAD_DOC/complete" -H "$AUTH")
echo "upload complete status=$(echo "$COMPLETE" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')"

echo ""
echo "=== Start review (S3-backed upload) ==="
REV=$(curl -fsS -X POST "$API/v1/projects/$PID/reviews" -H "$AUTH" -H 'Content-Type: application/json' \
  -d "{\"documentIds\":[\"$UPLOAD_DOC\"]}")
RID=$(echo "$REV" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
echo "reviewId=$RID"

echo ""
echo "=== Poll findings & status ==="
for i in $(seq 1 40); do
  ST=$(curl -fsS "$API/v1/reviews/$RID" -H "$AUTH")
  STATUS=$(echo "$ST" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  FC=$(curl -fsS "$API/v1/reviews/$RID/findings" -H "$AUTH" | python3 -c 'import sys,json; print(len(json.load(sys.stdin)))')
  echo "attempt $i: status=$STATUS findings=$FC"
  if [[ "$STATUS" == "completed" && "$FC" -gt 0 ]]; then break; fi
  sleep 0.25
done

FINDINGS=$(curl -fsS "$API/v1/reviews/$RID/findings" -H "$AUTH")
F1=$(echo "$FINDINGS" | python3 -c 'import sys,json; f=json.load(sys.stdin); print(f[0]["id"], f[0]["citations"][0]["quote"][:60])')
echo "first finding: $F1"

echo ""
echo "=== Snapshot document text (uploaded doc) ==="
SNAP=$(curl -fsS "$API/v1/reviews/$RID/snapshot" -H "$AUTH")
echo "$SNAP" | python3 -c '
import sys, json, os
snap = json.load(sys.stdin)
doc_id = os.environ["UPLOAD_DOC"]
text = snap.get("documents", {}).get(doc_id, "")
err = snap.get("documentErrors", {}).get(doc_id)
assert not err, err
assert "sub-processor" in text, "missing expected upload text in snapshot"
print("snapshot chars:", len(text))
'

echo ""
echo "=== WebSocket accept WITHOUT prior Show-in-document (python) ==="
python3 <<PY
import json, time, websocket, subprocess, os
api = os.environ.get("API", "http://127.0.0.1:8000").replace("http", "ws")
token = "$TOKEN"
rid = "$RID"
findings = json.loads("""$FINDINGS""")
f_accept = findings[0]
if len(findings) < 2:
    raise SystemExit("need at least 2 findings for accept+reject e2e")
f_reject = findings[1]

ws = websocket.create_connection(f"{api}/v1/reviews/{rid}/ws", timeout=10)
ws.send(json.dumps({"v":1,"type":"client.hello","payload":{"token":token,"lastSeq":0,"clientVersion":"e2e"}}))
welcome = json.loads(ws.recv())
assert welcome["type"] == "server.welcome", welcome
role = welcome["payload"]["role"]
print("ws role:", role)

def decide(f, action, reason=None):
    ws.send(json.dumps({
        "v":1,"type":"decision.submit",
        "payload":{"clientMsgId":"e2e-"+action,"findingId":f["id"],"action":action,"findingVersion":f["version"],"reason":reason}
    }))
    while True:
        msg = json.loads(ws.recv())
        if msg["type"] == "finding.updated":
            return msg
        if msg["type"] == "decision.rejected":
            raise SystemExit(f"decision rejected: {msg['payload']}")

msg = decide(f_accept, "accept")
print("accept:", msg["type"], msg["payload"]["finding"]["status"])

msg = decide(f_reject, "reject", reason="Not applicable to our processing scope")
print("reject:", msg["type"], msg["payload"]["finding"]["status"])

ws.close()
PY

echo ""
echo "=== Final tallies ==="
curl -fsS "$API/v1/reviews/$RID/findings" -H "$AUTH" | python3 -c '
import sys,json
fs=json.load(sys.stdin)
from collections import Counter
c=Counter(f["status"] for f in fs)
print(dict(c))
for f in fs[:2]:
    print(f["id"], f["status"], f["citations"][0]["quote"][:50])
'

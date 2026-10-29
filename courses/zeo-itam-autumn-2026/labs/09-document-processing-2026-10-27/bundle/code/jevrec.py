"""Ask Jev a typed question. Replays the saved answers;
when recording it makes the real call once, keeps a receipt for it
and records the answer. The key is read by keys.py and never printed."""
import datetime, hashlib, json, os
from pathlib import Path

SECRET = {"authorization", "proxy-authorization", "x-api-key",
          "api-key", "cookie", "set-cookie"}
sha = lambda b: hashlib.sha256(b).hexdigest()

def _norm(state, questions):
    q = {k: v.model_dump(exclude_none=True) for k, v in questions.items()}
    return json.loads(json.dumps({"state": state, "questions": q}))

def ask(call_id, state, questions):
    rec = Path("recorded") / f"jev-{call_id.split('-')[0]}.json"      # one file per section: s02-..., s04-...
    data = json.loads(rec.read_text()) if rec.exists() else {}
    want = _norm(state, questions)
    if not os.environ.get("RECORD"):
        got = data[call_id]
        assert got["asked"] == want, f"{call_id}: not the recorded question"
        return got["answers"]
    if call_id in data and data[call_id]["asked"] == want:
        return data[call_id]["answers"]
    import keys, httpx2, typesafe_sdk
    if not keys.load_jev_key():
        raise SystemExit("no key: not recorded")
    cap = {}
    class Tap(httpx2.BaseTransport):
        def __init__(self): self.inner = httpx2.HTTPTransport()
        def handle_request(self, request):
            cap["at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            cap["req"] = {"method": request.method, "url": str(request.url), "body": request.content}
            resp = self.inner.handle_request(request); resp.read()
            cap["resp"] = {"status": resp.status_code, "body": resp.content, "headers": {k: v for k, v in resp.headers.items() if k.lower() not in SECRET}}
            return resp
    with typesafe_sdk.TypeSafeClient(model="jev-latest", compression=False, http_client=httpx2.Client(transport=Tap())) as c:
        r = c.system_one(state=state, questions=questions)
    answers = {q: (dict(a.probabilities) if hasattr(a, "probabilities") else {"yes": a.noul}) for q, a in r.answers.items()}
    rdir = rec.parent / "receipts-jev"; rdir.mkdir(exist_ok=True)
    rq, rs = cap["req"], cap["resp"]
    (rdir / f"{call_id}.request.json").write_bytes(rq["body"])
    (rdir / f"{call_id}.response.json").write_bytes(rs["body"])
    (rdir / f"{call_id}.receipt.json").write_text(json.dumps({
        "call": call_id, "at_utc": cap["at"], "sdk": f"typesafe-sdk {typesafe_sdk.__version__}", "model_asked": "jev-latest",
        "method": rq["method"], "url": rq["url"], "status": rs["status"], "response_headers": rs["headers"],
        "request_sha256": sha(rq["body"]), "response_sha256": sha(rs["body"]), "answer": answers}, indent=1))
    data[call_id] = {"asked": want, "answers": answers, "request_sha256": sha(rq["body"]), "response_sha256": sha(rs["body"])}
    rec.write_text(json.dumps(data, indent=1))
    return json.loads(json.dumps(answers))        # the same shape as a replay (JSON keys are strings)

"""The OpenAI Agents API (sessions), not the Agents SDK. send() is the real request: client.beta.agents.sessions.create(agent=..., environment=..., input=...) starts a hosted session, and an events.create call adds the next input to it (the python client adds the OpenAI-Beta: agents=v1 header). The agent part is a plain dict: model, instructions and a list of JSON tool specs. By default lucy_session replays a saved run: the model's words come from the file, and our own tool functions run again on the saved arguments. With RECORD=1 it makes the real calls once and saves the run, the session items and a receipt (session id, turn id, model, time). The API key is read from a local key file and never printed or saved."""
import datetime, hashlib, json, os, time
from pathlib import Path

MODEL = "gpt-6-astra"
sha = lambda b: hashlib.sha256(b).hexdigest()

def send(client, request, environment, text, sid=None):
    """Start a session, or add an input to session sid."""
    sessions = client.beta.agents.sessions
    if sid is None:
        made = sessions.create(
            agent=request, environment=environment, input=text)
        return made.id
    message = {"type": "agent.session.input.message",
               "input": [{"role": "user", "content": [
                   {"type": "input_text", "text": text}]}]}
    sessions.events.create(sid, events=[message])
    return sid

class Run:
    def __init__(self, d):
        self.final_output, self.tool_calls, self.session_id, self.items = d["final"], d["tools"], d.get("session_id"), d.get("items", [])

def _rec(call_id): return Path("recorded") / f"agent-{call_id.split('-')[0]}.json"      # one file per section: s01-..., s02-...

def lucy_session(call_id, request, text, handlers, session=None, environment=None):
    """request: the agent part of the Agents API request (model, instructions, tools: plain JSON tool specs); handlers: {tool name: our function}; session: a name. The same name continues the same hosted session."""
    tools = handlers
    REC = _rec(call_id)
    data = json.loads(REC.read_text()) if REC.exists() else {}
    environment = environment or {"type": "openai_hosted"}
    want = {"input": text, "agent": request, "session": session, "environment": [f["path"] for f in environment.get("files", [])]}
    if not os.environ.get("RECORD") or (call_id in data and data[call_id]["asked"] == want):
        got = data[call_id]; assert got["asked"] == want, f"{call_id}: not the saved question"
        for t in got["run"]["tools"]: tools[t["name"]](**t["args"])           # our own code runs again, on the saved arguments
        return Run(got["run"])
    from openai import OpenAI
    from keys import openai_key
    key = openai_key()
    if not key: raise SystemExit("no OpenAI key: not recorded")
    client = OpenAI(api_key=key); sessions = client.beta.agents.sessions
    ids = {k: v["run"]["session_id"] for k, v in data.items() if v["asked"]["session"]}
    names = {v["asked"]["session"]: v["run"]["session_id"] for v in data.values() if v["asked"]["session"]}
    live = getattr(lucy_session, "_live", {}); lucy_session._live = live
    sid = live.get(session) if session else None
    sid = send(client, request, environment, text, sid)
    if session: live[session] = sid
    calls, turn = [], None
    finals = lambda: sum(1 for i in sessions.items.list(sid, order="asc", limit=100).data
                         if i.type == "message" and i.role == "assistant" and i.phase == "final_answer")
    before = live.get(("n", sid), 0)
    for _ in range(200):
        time.sleep(1.5)
        s = sessions.retrieve(sid)
        ra = getattr(s, "required_actions", None)
        if ra:
            for a in [x.to_dict() for x in ra]:
                out = tools[a["name"]](**a["arguments"]); turn = a["turn_id"]
                calls.append({"name": a["name"], "args": a["arguments"]})
                sessions.events.create(sid, events=[{"type": "agent.session.input.tool_result", "turn_id": a["turn_id"], "call_id": a["call_id"], "success": True, "output": out if isinstance(out, str) else json.dumps(out)}])
        elif s.status == "idle" and finals() > before: break
        elif s.status in ("failed", "cancelled"): raise SystemExit(f"{call_id}: session {s.status}")
    live[("n", sid)] = finals()
    items = [i.to_dict() for i in sessions.items.list(sid, order="asc", limit=100).data]
    last = [i for i in items if i.get("type") == "message" and i.get("role") == "assistant" and i.get("phase") == "final_answer"]
    final = "".join(c.get("text", "") for c in last[-1]["content"]) if last else ""
    brief = [{"type": i["type"], "role": i.get("role"), "phase": i.get("phase"), "name": i.get("name")} for i in items]
    run = {"final": final, "tools": calls, "session_id": sid, "items": brief}
    receipt = {"call": call_id, "at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "model": request["model"],
               "session_id": sid, "turn_id": turn, "items": len(items), "final_sha256": sha(final.encode()), "api": "openai-agents-api"}
    assert key not in json.dumps(run) + json.dumps(receipt)
    data[call_id] = {"asked": want, "run": run, "receipt": receipt}
    REC.parent.mkdir(parents=True, exist_ok=True); REC.write_text(json.dumps(data, indent=1))
    (REC.parent / "receipts-agent").mkdir(exist_ok=True); (REC.parent / "receipts-agent" / f"{call_id}.json").write_text(json.dumps(receipt, indent=1))
    return Run(run)

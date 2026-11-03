"""Offline tests for the Telegram steps (06 to 08, find_my_id): a small fake of three Telegram methods stands in for Telegram.
Run: python3 -m unittest test_transport"""
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))


class Fake:
    def __init__(self):
        self.updates, self.sent, self.fail_next, self.next_id = [], [], [], 100
        self.lock = threading.Lock()

    def push(self, text, user=5001, chat=5001):
        with self.lock:
            self.next_id += 1
            self.updates.append({"update_id": self.next_id, "message": {
                "chat": {"id": chat, "type": "private"}, "from": {"id": user}, "text": text}})


def make_server(fake):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, code, body):
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            params = json.loads(self.rfile.read(int(self.headers["Content-Length"])) or b"{}")
            method = self.path.rsplit("/", 1)[-1]
            if method == "getMe":
                return self.reply(200, {"ok": True, "result": {"username": "LucyShop_bot"}})
            if method == "sendMessage":
                fake.sent.append((params["chat_id"], params["text"]))
                return self.reply(200, {"ok": True, "result": {"message_id": len(fake.sent)}})
            if method == "getUpdates":
                if fake.fail_next:
                    return self.reply(fake.fail_next.pop(0), {"ok": False})
                offset, deadline = params.get("offset"), time.time() + min(params.get("timeout", 0), 1)
                while True:
                    with fake.lock:
                        if offset is not None:
                            fake.updates = [u for u in fake.updates if u["update_id"] >= offset]
                        found = list(fake.updates)
                    if found or time.time() >= deadline:
                        return self.reply(200, {"ok": True, "result": found})
                    time.sleep(0.02)
            self.reply(404, {"ok": False})
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class LabTests(unittest.TestCase):
    def setUp(self):
        self.fake = Fake()
        self.server = make_server(self.fake)
        self.dir = tempfile.mkdtemp()
        self.env = dict(os.environ, TELEGRAM_BOT_TOKEN="123:FAKE", PYTHONPATH=HERE,
                        TELEGRAM_API_BASE=f"http://127.0.0.1:{self.server.server_address[1]}")
        os.environ.update(TELEGRAM_BOT_TOKEN="123:FAKE", TELEGRAM_API_BASE=self.env["TELEGRAM_API_BASE"])
        self.old = os.getcwd()
        os.chdir(self.dir)
        for name in ("tg",):
            sys.modules.pop(name, None)
        sys.path.insert(0, HERE)
        global tg
        import tg

    def tearDown(self):
        os.chdir(self.old)
        self.server.shutdown()
        sys.path.remove(HERE)

    def run_step(self, name, *args):
        return subprocess.run([sys.executable, os.path.join(HERE, name), *args], cwd=self.dir, env=self.env,
                              capture_output=True, text=True, timeout=30)

    def test_step06_verifies_the_bot(self):
        self.assertIn("Verified @LucyShop_bot", self.run_step("step06_getme.py", "LucyShop_bot").stdout)
        self.assertIn("different bots", self.run_step("step06_getme.py", "other_bot").stderr)

    def test_step07_without_a_message_says_what_to_do(self):
        self.assertIn("Send it to this bot", self.run_step("step07_read.py").stderr)

    def test_step08_sends_to_the_chat_found_in_step07(self):
        self.fake.push("hello lucy", chat=777)
        self.run_step("step07_read.py")
        self.assertIn("accepted message", self.run_step("step08_send.py").stdout)
        self.assertEqual(self.fake.sent, [(777, "Hello from Lucy’s shop!")])

    def test_step08_before_step07_says_so(self):
        self.assertIn("Run step07_read.py first", self.run_step("step08_send.py").stderr)

    def test_step07_finds_hello_lucy_inside_longer_text(self):
        self.fake.push("Hello Lucy!")
        out = self.run_step("step07_read.py")
        self.assertIn("Received: Hello Lucy!", out.stdout)

    def pair(self, *args):
        import shutil
        if not os.path.exists(os.path.join(self.dir, "business.toml")):
            shutil.copy(os.path.join(HERE, "business.toml"), os.path.join(self.dir, "business.toml"))
        return self.run_step("find_my_id.py", *args)

    def owner_in_file(self):
        with open(os.path.join(self.dir, "business.toml")) as handle:
            return handle.read()

    def test_find_my_id_takes_the_sender_of_the_pairing_message(self):
        self.fake.push("hola", user=9999, chat=9999)
        self.fake.push("owner secretword", user=4242, chat=4242)
        out = self.pair("secretword")
        self.assertIn("owner_telegram_id = 4242", self.owner_in_file())
        self.assertIn("Saved your Telegram number", out.stdout)
        self.assertNotIn("4242", out.stdout + out.stderr)

    def test_find_my_id_ignores_messages_without_the_word_and_a_wrong_word(self):
        self.fake.push("owner otherword", user=5555, chat=5555)
        self.fake.push("hola", user=4242, chat=4242)
        out = self.pair("secretword")
        self.assertIn("No message 'owner <your word>' found", out.stderr)
        self.assertIn("owner_telegram_id = 0", self.owner_in_file())

    def test_find_my_id_never_replaces_an_owner_without_replace(self):
        self.pair("secretword")  # creates the file; no message yet
        path = os.path.join(self.dir, "business.toml")
        text = open(path).read().replace("owner_telegram_id = 0", "owner_telegram_id = 1111")
        open(path, "w").write(text)
        self.fake.push("owner secretword", user=4242, chat=4242)
        out = self.pair("secretword")
        self.assertIn("already has an owner", out.stderr)
        self.assertIn("owner_telegram_id = 1111", self.owner_in_file())
        self.pair("secretword", "--replace")
        self.assertIn("owner_telegram_id = 4242", self.owner_in_file())

    def test_find_my_id_refuses_when_two_people_send_the_word(self):
        self.fake.push("owner secretword", user=4242, chat=4242)
        self.fake.push("owner secretword", user=7777, chat=7777)
        out = self.pair("secretword")
        self.assertIn("More than one person", out.stderr)
        self.assertIn("owner_telegram_id = 0", self.owner_in_file())

    def test_find_my_id_needs_a_word(self):
        self.assertIn("Usage: python3 find_my_id.py", self.pair().stderr)

    def test_a_rejected_token_is_explained_without_printing_it(self):
        self.fake.fail_next.append(401)
        out = self.run_step("step07_read.py")
        self.assertIn("rejected the token (401)", out.stderr)
        self.assertNotIn("123:FAKE", out.stdout + out.stderr)

    def test_missing_token_says_how_to_add_one(self):
        env = {k: v for k, v in self.env.items() if k != "TELEGRAM_BOT_TOKEN"}
        result = subprocess.run([sys.executable, os.path.join(HERE, "step06_getme.py"), "x_bot"], cwd=self.dir,
                                env=env, capture_output=True, text=True, timeout=30)
        self.assertIn("TELEGRAM_BOT_TOKEN Codespaces secret", result.stderr)


if __name__ == "__main__":
    unittest.main()

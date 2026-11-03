"""Lucy's shop agent behind Telegram (lab 10).

Telegram only carries the messages. The brain is the course's always-on agent: one hosted Agents API session
for each chat (kept in SQLite, so Lucy remembers after a restart), Jev for the typed decisions, and the book's
Chapter 11 proposal and approval code. Nothing in the starter or the book is changed; this file wires them.

  python3 lucy.py            run Lucy until you press Ctrl+C
  python3 lucy.py --fake     a scripted demo with no network and no keys

Every incoming message, the decision made about it and the reply are logged below as sizes and labels. The text
people type is not logged, because it could hold a token.
"""
import argparse
import json
import logging
import os
import runpy
import sys
import tempfile
import time
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
STARTER = HERE.parents[2] / "projects" / "always-on-agent-starter"
log = logging.getLogger("lucy")
OWNER_ONLY = "Owner only. Solo la dueña o el dueño puede hacer eso."

TOOL_SPECS = [
    {"type": "function", "name": "stock", "description": "Current stock of every product: sku, name, tubs on hand, reorder point.",
     "parameters": {"type": "object", "properties": {}}},
    {"type": "function", "name": "propose_restock",
     "description": "Owner only. Draft an exact restock proposal for the owner to approve. Spends nothing.",
     "parameters": {"type": "object", "properties": {"sku": {"type": "string"}, "quantity": {"type": "integer"}}, "required": ["sku", "quantity"]}},
    {"type": "function", "name": "approve_restock",
     "description": "Owner only. Record the owner's approval of a proposal, after the owner has clearly said yes in their own message.",
     "parameters": {"type": "object", "properties": {"proposal_id": {"type": "string"}}, "required": ["proposal_id"]}},
]
APPROVAL_LABELS = {
    "approve": "The owner clearly says yes to the restock that was proposed: go ahead, approved, sí, adelante.",
    "reject": "The owner clearly says no, or asks to cancel or change it.",
    "unclear": "Anything else: a question, a different topic, a maybe, or a message that does not clearly answer the proposal.",
}
THRESHOLD = 0.7


def load_starter():
    """Import the starter's modules. The book's files open their neighbors by relative path, so this runs from the starter."""
    os.chdir(STARTER)
    if str(STARTER) not in sys.path:
        sys.path.insert(0, str(STARTER))
    import agent_runner, decision, schedule_daily  # noqa: E401
    from agent_session import AgentSession
    from enroll import EnrollBot, Enrollment
    channel = runpy.run_path("book/textbook/learner/profrod_sovereign_agent_ch09_messaging_learner.py")
    approval = runpy.run_path("book/textbook/learner/profrod_sovereign_agent_ch11_approval_learner.py")
    return dict(agent_runner=agent_runner, decision=decision, schedule_daily=schedule_daily, AgentSession=AgentSession,
                EnrollBot=EnrollBot, Enrollment=Enrollment, channel=channel, approval=approval)


def make_approval_question():
    from typesafe_sdk import Choice  # imported here so the offline tests need no SDK
    return {"action": Choice(instructions="Is this message from the shop owner a clear yes to the restock proposal?", criteria=APPROVAL_LABELS)}


def approval_label(jev, text, proposal, *, make_question=make_approval_question):
    """Jev classifies the owner's real message. Below the threshold, or on any failure, the answer is unclear."""
    try:
        reply = jev.system_one(state={"message": text, "proposal": proposal}, questions=make_question())
        probabilities = dict(reply.answers["action"].probabilities)
        label = max(probabilities, key=probabilities.get)
        return (label, probabilities[label]) if label in APPROVAL_LABELS and probabilities[label] >= THRESHOLD else ("unclear", probabilities.get(label, 0.0))
    except Exception as error:
        log.warning("approval decision failed, treated as unclear: %s", type(error).__name__)
        return "unclear", 0.0


class PresentationBot:
    """Wraps the messenger to remember the date Telegram gives each incoming message."""

    def __init__(self, bot, lucy):
        self.bot, self.lucy = bot, lucy

    @property
    def account(self):
        return self.bot.account

    def call(self, method, data):
        result = self.bot.call(method, data)  # raises OSError when the send did not succeed, so nothing is marked
        if method == "getUpdates":
            self.lucy.note_updates(result)
        return result


class Lucy:
    """The agent, its tools, and the owner check. The check is Python on Telegram's sender id, not the model's opinion."""

    def __init__(self, parts, config, bot, agent_client, jev, *, make_question=None, approval_question=make_approval_question, now=time.time, sleep=time.sleep):
        self.p, self.config, self.bot, self.jev, self.now = parts, config, bot, jev, now
        self.approval_question = approval_question
        self.owner_id = int(config["owner_telegram_id"])
        data = Path(config["data_dir"])
        data.mkdir(parents=True, exist_ok=True)
        wake = parts["schedule_daily"].WAKE
        self.db, self.queue = wake["open_shop"](str(data / "agent.db"))
        wake["seed_shop"](self.db)
        self.db.migrate("orders", parts["approval"]["ORDER_MIGRATIONS"])
        self.db.connection.row_factory = parts["approval"]["named_rows"]
        with self.db.immediate() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS lucy_dates (update_id INTEGER PRIMARY KEY, date INTEGER NOT NULL)")
            connection.execute("CREATE TABLE IF NOT EXISTS lucy_used_yes (work_id INTEGER PRIMARY KEY)")
            connection.execute("CREATE TABLE IF NOT EXISTS lucy_pending (chat TEXT PRIMARY KEY, proposal_id TEXT NOT NULL, digest TEXT NOT NULL, work_id INTEGER NOT NULL, presented INTEGER NOT NULL DEFAULT 0, presented_at INTEGER NOT NULL DEFAULT 0)")
        self.enrollment = parts["Enrollment"](str(data / "enrolled.db"))
        self.wrapped = parts["EnrollBot"](PresentationBot(bot, self), self.enrollment, config["join_code"], config["welcome"])
        self.assignment = None
        self.session = parts["AgentSession"](
            agent_client, str(data / "sessions.db"), model=config["model"], instructions=config["instructions"], tools=TOOL_SPECS,
            handlers={"stock": lambda: wake["stock_rows"](self.db.connection), "propose_restock": self.propose_restock, "approve_restock": self.approve_restock}, sleep=sleep)
        self.last_label = "n/a"
        owner_route = ("telegram:" + bot.account, str(self.owner_id))
        decide = lambda text: self._decide(text, make_question)  # noqa: E731
        parts["agent_runner"].install(parts["channel"], self.session, decide=decide, owner_route=owner_route)
        namespace = parts["channel"]["serve"].__globals__
        inner = namespace["run_claim"]
        namespace["run_claim"] = lambda db, queue, assignment, model: self._run(inner, db, queue, assignment, model)

    def _decide(self, text, make_question):
        kwargs = {"make_question": make_question} if make_question else {}
        label = self.p["decision"].decide(self.jev, text, **kwargs)[0]
        self.last_label = label
        return label

    def _run(self, inner, db, queue, assignment, model):
        self.assignment, self.last_label = assignment, "n/a"
        role = "owner" if self.is_owner(assignment) else "customer"
        started = time.time()
        try:
            result = inner(db, queue, assignment, model)
        finally:
            self.assignment = None
        log.info("%s message in (%d characters); decision %s; done in %.1fs", role, len(assignment.text), self.last_label, time.time() - started)
        return result

    def is_owner(self, assignment):
        who = assignment.session_id.rsplit(":", 1)[-1]
        return who.isdigit() and int(who) == self.owner_id

    def propose_restock(self, sku, quantity):
        if self.assignment is None or not self.is_owner(self.assignment):
            return OWNER_ONLY
        ch11 = self.p["approval"]
        ch11["hold"](self.db, self.assignment)
        proposal_id = ch11["propose"](self.db, self.assignment, sku, int(quantity))
        row = self.db.connection.execute("SELECT proposal, amount, status, digest FROM assistant_orders WHERE id=?", (proposal_id,)).fetchone()
        chat = self.assignment.session_id
        self._supersede(chat, proposal_id)
        with self.db.immediate() as connection:
            connection.execute("INSERT OR REPLACE INTO lucy_pending(chat, proposal_id, digest, work_id, presented) VALUES (?,?,?,?,0)", (chat, proposal_id, row["digest"], self.assignment.work_id))
        proposal = json.loads(row["proposal"])
        shown = self.show_proposal(proposal_id, proposal, row["amount"])
        log.info("owner proposal drafted for %s x %s; shown to the owner: %s", proposal["sku"], proposal["quantity"], "yes" if shown else "no")
        note = ("The program has sent the owner the exact proposal. Tell the owner, in their language, to reply with a clear yes in a new message."
                if shown else "The owner could not be reached, so the proposal cannot be approved yet. Tell the owner, and ask them to send /start to the bot.")
        return {"proposal_id": proposal_id, "sku": proposal["sku"], "quantity": proposal["quantity"], "total_cents": row["amount"],
                "status": row["status"], "reference": proposal_id[:8], "next": note + " Nothing is ordered."}

    def note_updates(self, updates):
        """Remember when Telegram says each message was sent, so a yes sent before the proposal was shown can be told apart."""
        with self.db.immediate() as connection:
            for update in updates if isinstance(updates, list) else []:
                date = update.get("message", {}).get("date") if isinstance(update, dict) else None
                if type(update.get("update_id")) is int and type(date) is int:
                    connection.execute("INSERT OR IGNORE INTO lucy_dates VALUES (?,?)", (update["update_id"], date))

    def show_proposal(self, proposal_id, proposal, total_cents):
        """The program itself sends the owner the exact proposal, in its own words, not the model's. Only a send that
        Telegram receipted (a positive message id) counts as shown; anything else leaves the proposal unapprovable."""
        ref = proposal_id[:8]
        text = ("Proposal %s: %d tubs of %s at %d cents each, %d cents in all. Nothing is ordered. Reply with a clear yes to approve it. / "
                "Propuesta %s: %d tubs de %s a %d centavos cada uno, %d centavos en total. No se pide nada. Responde con un sí claro para aprobarla."
                % (ref, proposal["quantity"], proposal["sku"], proposal["unit_cost_cents"], total_cents,
                   ref, proposal["quantity"], proposal["sku"], proposal["unit_cost_cents"], total_cents))
        try:
            receipt = self.bot.call("sendMessage", {"chat_id": self.owner_id, "text": text})
        except OSError as error:
            log.warning("could not show the proposal to the owner (%s)", type(error).__name__)
            return False
        if not (isinstance(receipt, dict) and type(receipt.get("message_id")) is int and receipt["message_id"] > 0):
            log.warning("the proposal was not receipted by Telegram")
            return False
        if type(receipt.get("date")) is not int or receipt["date"] <= 0:
            log.warning("Telegram's receipt had no date, so the order of messages cannot be checked")
            return False
        sent = receipt["date"]  # Telegram's own time, the same clock as the dates of incoming messages
        with self.db.immediate() as connection:
            connection.execute("UPDATE lucy_pending SET presented=1, presented_at=? WHERE proposal_id=?", (sent, proposal_id))
        return True

    def _sent_after(self, work_id, moment):
        """True when Telegram dated the message that made this work item later than `moment`. Unknown counts as not later."""
        row = self.db.connection.execute("SELECT source_id FROM work WHERE work_id=?", (work_id,)).fetchone()
        try:
            update_id = int(row["source_id"].rsplit(":", 1)[-1])
        except (TypeError, ValueError):
            return False
        date = self.db.connection.execute("SELECT date FROM lucy_dates WHERE update_id=?", (update_id,)).fetchone()
        return date is not None and date["date"] > moment

    def _supersede(self, chat, new_id):
        """Only the proposal just shown can be approved. An older open one is revoked, so a later yes cannot reach it."""
        old = self.db.connection.execute("SELECT proposal_id FROM lucy_pending WHERE chat=?", (chat,)).fetchone()
        if old and old["proposal_id"] != new_id:
            ch11 = self.p["approval"]
            policy = ch11["SpendingPolicy"](operators=frozenset({str(self.owner_id)}))
            ch11["revoke"](self.db, old["proposal_id"], actor=str(self.owner_id), policy=policy)

    def approve_restock(self, proposal_id):
        if self.assignment is None or not self.is_owner(self.assignment):
            return OWNER_ONLY
        connection = self.db.connection
        chat = self.assignment.session_id
        pending = connection.execute("SELECT proposal_id, digest, work_id, presented, presented_at FROM lucy_pending WHERE chat=?", (chat,)).fetchone()
        if pending is None:
            return "Nothing is waiting for the owner's yes. Ask for a proposal first."
        if connection.execute("SELECT 1 FROM lucy_used_yes WHERE work_id=?", (self.assignment.work_id,)).fetchone():
            return "Not approved: this message of the owner has already been used for an approval."
        if not pending["presented"]:
            return "Not approved: the proposal has not been shown to the owner yet. The owner must receive it first, then say yes in a new message."
        if pending["work_id"] == self.assignment.work_id:
            return "Not approved: the owner must say yes in a new message, after seeing the proposal."
        if proposal_id != pending["proposal_id"]:
            return "Not approved: that is not the proposal shown to the owner. The proposal waiting is " + pending["proposal_id"] + "."
        if not self._sent_after(self.assignment.work_id, pending["presented_at"]):
            return "Not approved: that message was sent before the proposal was shown to the owner. Ask for the yes again now."
        order = connection.execute("SELECT id, proposal, digest, status FROM assistant_orders WHERE id=?", (proposal_id,)).fetchone()
        if order is None or order["digest"] != pending["digest"] or order["status"] != "DRAFT":
            return "No open proposal with that id."
        text = self.assignment.text  # the owner's real message, taken from the queue, not from the model
        label, probability = approval_label(self.jev, text, order["proposal"], make_question=self.approval_question)
        log.info("approval decision %s (%.2f)", label, probability)
        if label != "approve":
            return "Not approved: the owner's message was not a clear yes to this exact proposal. Ask again."
        ch11 = self.p["approval"]
        policy = ch11["SpendingPolicy"](operators=frozenset({str(self.owner_id)}))
        ch11["approve"](self.db, order["id"], order["digest"], actor=str(self.owner_id), policy=policy, expires=time.time() + 3600)
        with self.db.immediate() as connection:  # the yes is used up: a second yes cannot approve anything else
            connection.execute("DELETE FROM lucy_pending WHERE chat=?", (chat,))
            connection.execute("INSERT OR IGNORE INTO lucy_used_yes VALUES (?)", (self.assignment.work_id,))
        return "Approved and recorded for one hour. Nothing is ordered: this lab never sends an order to a supplier."

    def one_round(self):
        wake, channel = self.p["schedule_daily"].WAKE, self.p["channel"]
        wake["tick"](self.db, self.queue, now=time.time())
        operators = frozenset({self.owner_id}) | self.enrollment.customers()
        return channel["serve"](self.db, self.queue, self.wrapped, operators, lambda: None, rounds=1)

    def guarded_round(self, sleep=time.sleep, retry=5):
        """One round. A failed Telegram call is logged by class name and tried again after a pause."""
        try:
            return self.one_round()
        except OSError as error:
            log.warning("round failed (%s); trying again in %d seconds", type(error).__name__, retry)
            sleep(retry)
            return {}

    def close(self):
        self.session.close()
        self.enrollment.close()
        self.db.connection.close()


def real_clients(channel):
    keys = {name: channel["secret"](name) for name in ("OPENAI_API_KEY", "TYPESAFE_API_KEY")}
    missing = [name for name, value in keys.items() if not value]
    if missing:
        raise SystemExit("Missing Codespaces secret: " + ", ".join(missing))
    from openai import OpenAI
    from typesafe_sdk import TypeSafeClient
    return OpenAI(api_key=keys["OPENAI_API_KEY"]), TypeSafeClient(model="jev-latest", api_key=keys["TYPESAFE_API_KEY"])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fake", action="store_true", help="scripted demo, no network, no keys")
    parser.add_argument("--config", default=str(HERE / "business.toml"))
    args = parser.parse_args()
    logging.basicConfig(format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S", level=logging.INFO)
    config = tomllib.loads(Path(args.config).read_text())
    config["data_dir"] = str(Path(args.config).resolve().parent / config["data_dir"])
    parts = load_starter()
    if args.fake:
        sys.exit(fake_demo(parts, config))
    if not config["owner_telegram_id"] or config["join_code"] == "CHANGE-ME":
        raise SystemExit("Set owner_telegram_id (run find_my_id.py) and join_code in business.toml first.")
    token = parts["channel"]["secret"]("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("No bot token found. Add the TELEGRAM_BOT_TOKEN Codespaces secret, or run: source set_token.sh")
    bot = parts["channel"]["Telegram"](token)
    agent_client, jev = real_clients(parts["channel"])
    lucy = Lucy(parts, config, bot, agent_client, jev)
    log.info("Lucy is listening. Message your bot on Telegram. Press Ctrl+C to stop.")
    try:
        while True:
            summary = lucy.guarded_round()
            if not summary.get("admitted"):
                time.sleep(1)
    except KeyboardInterrupt:
        log.info("Stopped. New messages now wait until you start lucy.py again.")
    finally:
        lucy.close()


def fake_demo(parts, config):
    """Scripted run on the starter's fakes: an owner proposal, a yes, and a customer who is refused."""
    sys.path.insert(0, str(STARTER))
    from fake_agents import FakeAgentsClient, FakeJev
    from fake_messenger import FakeMessenger
    with tempfile.TemporaryDirectory() as scratch:
        config.update(owner_telegram_id=1001, data_dir=scratch, join_code="DEMO")
        bot = FakeMessenger()
        agent = FakeAgentsClient(lambda text: ("say", "Hola. Hello."))
        jev = FakeJev(lambda text: {"answer": 0.9, "ask_owner": 0.08, "refuse": 0.02})
        lucy = Lucy(parts, config, bot, agent, jev, make_question=lambda: {}, sleep=lambda seconds: None)
        bot.push(2002, "/start DEMO")
        lucy.guarded_round(sleep=lambda seconds: None)
        bot.push(2002, "tienes vainilla?")
        for _ in range(4):
            lucy.guarded_round(sleep=lambda seconds: None)
        for message in bot.sent:
            print(message["chat_id"], "<-", message["text"])
        lucy.close()
    return 0


if __name__ == "__main__":
    main()

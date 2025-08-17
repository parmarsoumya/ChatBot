from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
import re, datetime, csv, os, time, random
from difflib import get_close_matches

console = Console()

PUNCT_RE = re.compile(r"[^\w\s]")
def normalize(text: str) -> str:
    return PUNCT_RE.sub(" ", text.lower()).strip()

def now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def type_print(msg: str, delay: float = 0.015):
    """Typing effect for bot messages"""
    for ch in msg:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()

FAQ = {
    "what are your hours": "🕒 We’re open Mon–Sat 9am–6pm and Sun 10am–4pm.",
    "how do i track my order": "📦 Track it in your account → Orders → Track. Or share your Order ID here!",
    "what is your return policy": "↩️ 30-day hassle-free returns. Refunds go back to your original payment method.",
    "how long does shipping take": "🚚 Standard: 3–6 business days | Express: 1–2 business days.",
    "how can i contact support": "☎️ Email: support@example.com | Phone: +1-555-0100",
    "do you ship internationally": "🌍 Yes! Duties/taxes depend on the destination.",
    "how do i cancel my order": "❌ If it hasn’t shipped, I can request cancellation. Share your Order ID.",
    "do you offer warranty": "🛡️ Most items have a 1-year manufacturer warranty. Keep your invoice.",
}

FAQ_KEYS = list(FAQ.keys())
FAQ_KEYS_NORM = [normalize(k) for k in FAQ_KEYS]

INTENT_PATTERNS = {
    "greet": r"\b(hi|hello|hey|namaste)\b",
    "bye": r"\b(bye|goodbye|see you|exit|quit)\b",
    "thanks": r"\b(thanks|thank you|ty)\b",
    "help": r"\b(help|options|menu|what can you do)\b",
    "handoff": r"\b(agent|human|representative)\b",
    "refund": r"\b(refund|return|replace)\b",
    "shipping": r"\b(ship|shipping|delivery|arrive|track)\b",
    "billing": r"\b(bill|payment|charged|invoice)\b",
    "contact": r"\b(contact|email|phone|support)\b",
    "hours": r"\b(hour|timing|open|closing)\b",
    "faq": r"\b(faq|questions|options)\b",
    "time": r"\b(time|date|today|now)\b",
    "summary": r"\b(summary|log|history)\b",
    "clear": r"\b(clear logs|reset logs)\b",
    "about": r"\b(about|who are you|company|bot)\b",
}

ORDER_ID_RE = re.compile(r"\b(?:ORD|ORDER)[-\s]?(\d{6,12})\b", flags=re.I)

ORDER_STATUSES = [
    "🟢 Confirmed", "📦 Packed", "🚚 Out for delivery", "✅ Delivered",
    "⚠️ Delayed due to weather", "🛑 On Hold - Payment Issue"
]

def detect_intent(text: str):
    for intent, pat in INTENT_PATTERNS.items():
        if re.search(pat, text, flags=re.I):
            return intent
    return None

class Chatbot:
    def __init__(self, company="Acme"):
        self.company = company
        self.session_id = f"session-{int(datetime.datetime.now().timestamp())}"
        self.logs = []
        self.user_name = None

    def log(self, speaker, text):
        self.logs.append((now(), speaker, text))
        fn = "chat_logs.csv"
        write_header = not os.path.exists(fn)
        with open(fn, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if write_header:
                w.writerow(["time", "speaker", "message"])
            w.writerow([now(), speaker, text])

    def respond(self, user_text: str) -> str:
        if not user_text.strip():
            return "⚠️ Please type something."

        self.log("user", user_text)

        if re.search(INTENT_PATTERNS["bye"], user_text, re.I):
            return "👋 Thanks for chatting! Have a wonderful day!"

        oid = ORDER_ID_RE.search(user_text)
        if oid:
            order_id = oid.group(1)
            status = random.choice(ORDER_STATUSES)
            return f"📦 Order {order_id}: Status → {status}"

        intent = detect_intent(user_text) or "unknown"

        if intent == "greet":
            if not self.user_name:
                self.user_name = Prompt.ask("[bold cyan]🤖 May I know your name?[/bold cyan]")
                return f"👋 Hello {self.user_name}, welcome to {self.company} support!"
            return f"🤖 Hello {self.user_name or 'friend'}! How can I help today?"
        elif intent == "help":
            return "💡 You can ask about: shipping, refunds, billing, hours, contact info, or type `faq`."
        elif intent == "thanks":
            return "🙏 You’re most welcome!"
        elif intent == "handoff":
            return "👨‍💼 Connecting you to a human agent shortly..."
        elif intent == "refund":
            return "↩️ Please share your Order ID for processing your return."
        elif intent == "shipping":
            return "🚚 Please share your Order ID so I can check shipping status."
        elif intent == "billing":
            return "💳 Let’s check billing. Can you provide your Order ID?"
        elif intent == "contact":
            return FAQ["how can i contact support"]
        elif intent == "hours":
            return FAQ["what are your hours"]
        elif intent == "faq":
            faq_list = "\n".join([f"• {q}" for q in FAQ_KEYS])
            return f"📖 Here are common questions:\n{faq_list}"
        elif intent == "time":
            return f"⏰ Current date & time: {now()}"
        elif intent == "summary":
            return self.show_summary()
        elif intent == "clear":
            open("chat_logs.csv", "w").close()
            return "🗑️ Logs cleared successfully."
        elif intent == "about":
            return f"🤖 I’m {self.company} Bot! I help with orders, refunds, shipping & more."

        matches = get_close_matches(normalize(user_text), FAQ_KEYS_NORM, n=1, cutoff=0.6)
        if matches:
            idx = FAQ_KEYS_NORM.index(matches[0])
            return FAQ[FAQ_KEYS[idx]]

        return "🤔 I’m not sure. Try rephrasing or type `help`."

    def show_summary(self) -> str:
        if not self.logs:
            return "📋 No conversation history yet."
        history = "\n".join([f"[{t}] {speaker}: {msg}" for t, speaker, msg in self.logs])
        return f"📋 Conversation Summary:\n{history}"

def main():
    bot = Chatbot("Acme")
    console.print(Panel.fit("💬 [bold green]Customer Support Chatbot[/bold green] 🤖", border_style="bright_blue"))
    type_print(bot.respond("hello"))

    while True:
        try:
            user = Prompt.ask("\n[bold cyan]You[/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            break
        reply = bot.respond(user)
        console.print(Panel.fit(f"[yellow]{reply}[/yellow]", border_style="green"))
        bot.log("bot", reply)
        if re.search(INTENT_PATTERNS["bye"], user, re.I):
            break

if __name__ == "__main__":
    main()

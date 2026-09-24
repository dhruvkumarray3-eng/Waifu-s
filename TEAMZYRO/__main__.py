# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

from TEAMZYRO import *
import importlib
import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram.enums import ParseMode
from TEAMZYRO.modules import ALL_MODULES
from TEAMZYRO.unit.zyro_emoji import premium


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - WaifuBot is alive!")

    def log_message(self, format, *args):
        pass  # Suppress HTTP access logs from cluttering bot logs


def start_health_server():
    port = int(os.environ.get("PORT", 8000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        LOGGER("TEAMZYRO").info(f"Health check HTTP server listening on port {port}")
        server.serve_forever()
    except Exception as e:
        LOGGER("TEAMZYRO").warning(f"Could not start health check HTTP server on port {port}: {e}")


def main() -> None:
    # Start background HTTP health check server for Koyeb / Render / Heroku
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    for module_name in ALL_MODULES:
        imported_module = importlib.import_module("TEAMZYRO.modules." + module_name)
    LOGGER("TEAMZYRO.modules").info("𝐀𝐥𝐥 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬 𝐋𝐨𝐚𝐝𝐞𝐝 𝐁𝐚𝐛𝐲🥳...")

    ZYRO.start()

    # Verify FORCE_JOIN admin permissions only when a chat ID/username is configured.
    # The bot can still run without force-join enforcement.
    import sys
    import TEAMZYRO
    if FORCE_JOIN:
        try:
            try:
                chat_target = int(FORCE_JOIN)
            except ValueError:
                chat_target = FORCE_JOIN

            chat_obj = ZYRO.get_chat(chat_target)
            invite_link = chat_obj.invite_link
            if not invite_link:
                invite = ZYRO.create_chat_invite_link(chat_target)
                invite_link = invite.invite_link

            TEAMZYRO.FORCE_JOIN_LINK = invite_link
            LOGGER("TEAMZYRO").info(
                f"Successfully verified FORCE_JOIN admin rights. Link: {invite_link}"
            )
        except Exception as e:
            LOGGER("TEAMZYRO").error(
                "\n"
                "=======================================================================\n"
                "❌ FORCE_JOIN verification failed; continuing without force-join:\n"
                f"{e}\n"
                "======================================================================="
            )
    else:
        LOGGER("TEAMZYRO").warning(
            "FORCE_JOIN is not configured; force-join checks are disabled."
        )

    # Send a startup message only when a logging chat is configured.
    if BOT_LOGGING:
        try:
            try:
                log_target = int(BOT_LOGGING)
            except ValueError:
                log_target = BOT_LOGGING

            test_msg = ZYRO.send_message(
                chat_id=log_target,
                text=(
                    f"{premium(0, '⚙️')} <b>WaifuBot Startup Notification</b>\n"
                    f"{premium(1, '✅')} Successfully connected to the logs channel."
                ),
                parse_mode=ParseMode.HTML,
            )
            LOGGER("TEAMZYRO").info(
                f"Startup log sent successfully (ID: {test_msg.id})."
            )
        except Exception as e:
            LOGGER("TEAMZYRO").warning(
                f"BOT_LOGGING is configured but unavailable; continuing: {e}"
            )
    else:
        LOGGER("TEAMZYRO").warning(
            "BOT_LOGGING is not configured; startup notifications are disabled."
        )

    application.run_polling(drop_pending_updates=True)
    LOGGER("TEAMZYRO").info(
        "╔═════ஜ۩۞۩ஜ════╗\n  ☠︎︎MADE BY TEAMZYRO☠︎︎\n╚═════ஜ۩۞۩ஜ════╝"
    )
    send_start_message()
    

if __name__ == "__main__":
    main()
    
    

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
from TEAMZYRO.modules import ALL_MODULES


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

    # Verify FORCE_JOIN admin permissions and get/generate invite link
    import sys
    import TEAMZYRO
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
        LOGGER("TEAMZYRO").info(f"Successfully verified FORCE_JOIN admin rights. Link: {invite_link}")
    except Exception as e:
        LOGGER("TEAMZYRO").error(
            "\n"
            "=======================================================================\n"
            "❌ CRITICAL STARTUP ERROR:\n"
            f"Bot is NOT an admin in the FORCE_JOIN channel/chat ({FORCE_JOIN})!\n"
            "Please ensure the bot is added to the channel as an Admin and has\n"
            "permission to invite users.\n"
            f"Details: {e}\n"
            "======================================================================="
        )
        try:
            ZYRO.stop()
        except:
            pass
        sys.exit(1)

    # Verify BOT_LOGGING permissions by sending a startup message
    try:
        try:
            log_target = int(BOT_LOGGING)
        except ValueError:
            log_target = BOT_LOGGING
            
        test_msg = ZYRO.send_message(
            chat_id=log_target,
            text="⚙️ **WaifuBot Startup Notification**:\nSuccessfully connected & verified write permissions in the logs channel!"
        )
        LOGGER("TEAMZYRO").info(f"Successfully verified BOT_LOGGING permissions. Test message sent (ID: {test_msg.id}).")
    except Exception as e:
        LOGGER("TEAMZYRO").error(
            "\n"
            "=======================================================================\n"
            "❌ CRITICAL STARTUP ERROR:\n"
            f"Bot cannot post/send messages to BOT_LOGGING chat ({BOT_LOGGING})!\n"
            "Please ensure the bot is added to the log channel/group and has permission\n"
            "to post messages.\n"
            f"Details: {e}\n"
            "======================================================================="
        )
        try:
            ZYRO.stop()
        except:
            pass
        sys.exit(1)

    application.run_polling(drop_pending_updates=True)
    LOGGER("TEAMZYRO").info(
        "╔═════ஜ۩۞۩ஜ════╗\n  ☠︎︎MADE BY TEAMZYRO☠︎︎\n╚═════ஜ۩۞۩ஜ════╝"
    )
    send_start_message()
    

if __name__ == "__main__":
    main()
    
    

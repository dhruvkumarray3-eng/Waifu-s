---
name: Telegram custom emoji handling
description: Pyrogram custom emoji markup and safe group departure behavior
---

Use Pyrogram HTML custom emoji tags in outgoing messages: `<tg-emoji emoji-id="...">fallback</tg-emoji>`. Keep fallback text so messages remain readable if an emoji asset is unavailable.

**Why:** Pyrogram parses this tag into `MessageEntityCustomEmoji`, while inline keyboard labels cannot use message HTML entities. Group departure explanations must be sent before calling `leave_chat`, because the bot cannot reliably post after it leaves.

**How to apply:** Use the shared emoji helpers for HTML-formatted bot messages and send any small-group explanation before leaving. Keep button labels as ordinary Unicode text.
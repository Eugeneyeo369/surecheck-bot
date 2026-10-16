import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I’m SURE Check.\n\n"
        "Send me a suspicious headline, claim, or message and I’ll guide you through a quick verification check."
    )


async def receive_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["claim"] = update.message.text

    keyboard = [
        [InlineKeyboardButton("Official source", callback_data="source_official")],
        [InlineKeyboardButton("News outlet", callback_data="source_news")],
        [InlineKeyboardButton("Friend / group chat", callback_data="source_friend")],
        [InlineKeyboardButton("Unknown", callback_data="source_unknown")],
    ]

    await update.message.reply_text(
        f'You sent:\n"{update.message.text}"\n\n'
        "Step 1: SOURCE\nWho is the original source of this information?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("source_"):
        context.user_data["source"] = data

        keyboard = [
            [InlineKeyboardButton("Yes", callback_data="confirm_yes")],
            [InlineKeyboardButton("No", callback_data="confirm_no")],
            [InlineKeyboardButton("Not sure", callback_data="confirm_unsure")],
        ]

        await query.edit_message_text(
            "Step 2: RESEARCH\n"
            "Can you find another credible source that confirms the same claim?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data.startswith("confirm_"):
        context.user_data["confirmation"] = data

        keyboard = [
            [InlineKeyboardButton("Yes", callback_data="warning_yes")],
            [InlineKeyboardButton("No", callback_data="warning_no")],
            [InlineKeyboardButton("Not sure", callback_data="warning_unsure")],
        ]

        await query.edit_message_text(
            "Step 3: EVALUATE\n"
            "Does the post use emotional language, urgency, shocking wording, or seem to lack context?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data.startswith("warning_"):
        context.user_data["warning"] = data

        source = context.user_data.get("source")
        confirmation = context.user_data.get("confirmation")
        warning = context.user_data.get("warning")

        if confirmation == "confirm_yes" and warning == "warning_no":
            result = (
                "Assessment: LIKELY CREDIBLE\n\n"
                "Another credible source supports the claim and there are fewer obvious warning signs.\n\n"
                "Next step: Check that the sources are referring to the same event, date, and context before sharing."
            )

        elif confirmation == "confirm_no" or source == "source_unknown" or warning == "warning_yes":
            result = (
                "Assessment: POTENTIALLY MISLEADING\n\n"
                "There are verification gaps or warning signs in this claim.\n\n"
                "Next step: Check an official source, search reputable news outlets, or use reverse image search before sharing."
            )

        else:
            result = (
                "Assessment: NEEDS MORE VERIFICATION\n\n"
                "There is not enough information to confidently assess this claim yet.\n\n"
                "Next step: Look for an independent credible source and check the original context."
            )

        await query.edit_message_text(
            result + "\n\nSend another claim anytime to start again."
        )


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_claim))

print("Bot is running...")
app.run_polling()
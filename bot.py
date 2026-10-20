import json, random, string
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ====== YOUR CONFIG ======
TOKEN = "8749845591:AAF82rvT7gyGhhfVo39udEf8n6Vm_fS9y0A"
ADMIN_USERNAME = "tradexa_support"
ADMIN_ID = 7608285065  # YOU
BOT_NAME = "TRADEXA AI"
USERS_FILE = "users.json"
LICENSES_FILE = "licenses.json"
MASTER_FILE = "master_ssid.json"

def load(f, d):
    try: return json.load(open(f))
    except: return d
def save(f, data): json.dump(data, open(f,'w'), indent=2)
def new_license():
    return f"TRADEXA-{''.join(random.choices(string.ascii_uppercase+string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase+string.digits, k=4))}"
def valid_ssid(s): return len(s) > 60

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Start Copying", callback_data="start_copy")],
        [InlineKeyboardButton("📜 License History", callback_data="history"),
         InlineKeyboardButton("⏹️ Stop Copying", callback_data="stop")],
        [InlineKeyboardButton("📞 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME}")],
        [InlineKeyboardButton("ℹ️ About TRADEXA AI", callback_data="about")]
    ])
def back_kb(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="back")]])
def license_kb(): return InlineKeyboardMarkup([[InlineKeyboardButton("📞 Contact @tradexa_support", url=f"https://t.me/{ADMIN_USERNAME}")],[InlineKeyboardButton("🔙 Back", callback_data="back")]])
def ssid_kb(): return InlineKeyboardMarkup([[InlineKeyboardButton("❓ How to get SSID?", callback_data="how_ssid")],[InlineKeyboardButton("🔙 Back", callback_data="back")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        f"🚀 *{BOT_NAME} - OFFICIAL*\n\n"
        "Welcome to the Smart Copy Trading System!\n\n"
        "✅ Copy my live trades automatically\n"
        "✅ Works even when you are offline\n"
        "✅ Trades open on your Pocket Option\n"
        "✅ Min capital ₦1,000\n\n"
        "👇 *Choose option:*"
    )
    if update.message: await update.message.reply_text(msg, reply_markup=main_kb(), parse_mode='Markdown')
    else: await update.callback_query.edit_message_text(msg, reply_markup=main_kb(), parse_mode='Markdown')

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); d = q.data
    if d == "back": await start(update, context)
    elif d == "about":
        await q.edit_message_text("ℹ️ *TRADEXA AI*\n\nWe are a team of expert traders. This bot copies master trades to your account with your chosen %.\n\nAdmin: @tradexa_support", reply_markup=back_kb(), parse_mode='Markdown')
    elif d == "start_copy":
        context.user_data['step'] = 'license'
        await q.edit_message_text("🔑 *STEP 1/3: Enter License*\n\nFormat: `TRADEXA-XXXX-XXXX`\n\nNo license? Contact @tradexa_support", reply_markup=license_kb(), parse_mode='Markdown')
    elif d == "how_ssid":
        await q.edit_message_text("❓ *How to get Pocket Option SSID*\n\n1. Chrome → pocketoption.com → Login\n2. F12 → Application Tab → Cookies → https://pocketoption.com\n3. Copy `ssid` value (very long string starting with 42...)\n4. Paste here\n\nKeep it secret!", reply_markup=back_kb(), parse_mode='Markdown')
    elif d == "history":
        users = load(USERS_FILE, {}); uid = str(q.from_user.id)
        if uid not in users: await q.edit_message_text("❌ No license found. Start copying first.", reply_markup=back_kb()); return
        u = users[uid]; exp = datetime.fromtimestamp(u['expiry']); act = datetime.fromtimestamp(u['activated']); days = (exp - datetime.now()).days
        await q.edit_message_text(f"📜 *License History - {BOT_NAME}*\n\nLicense: `{u['license']}`\nActivated: {act.strftime('%d/%m/%Y')}\nExpires: {exp.strftime('%d/%m/%Y')}\nDays Left: {max(0,days)}\nCopy: {u['percent']}%\nStatus: {'🟢 COPYING' if u['copying'] and days>=0 else '🔴 STOPPED'}", reply_markup=back_kb(), parse_mode='Markdown')
    elif d == "stop":
        users = load(USERS_FILE, {}); uid = str(q.from_user.id)
        if uid in users: users[uid]['copying']=False; save(USERS_FILE, users); await q.edit_message_text("⏹️ *Copying Stopped!*", reply_markup=back_kb(), parse_mode='Markdown')
        else: await q.edit_message_text("❌ Nothing to stop.", reply_markup=back_kb())

async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip(); uid = str(update.from_user.id); is_admin = update.from_user.id == ADMIN_ID
    step = context.user_data.get('step')

    if text.startswith('/genlicense'):
        if not is_admin: await update.message.reply_text("❌ Admin only."); return
        licenses = load(LICENSES_FILE, {})
        try: days = int(text.split()[1])
        except: days = 30
        lic = new_license(); licenses[lic] = {"days": days, "used": False, "created": datetime.now().timestamp()}; save(LICENSES_FILE, licenses)
        await update.message.reply_text(f"✅ *License Generated*\n\n`{lic}`\n{days} days\n\nSend this to customer.", parse_mode='Markdown'); return
    if text.startswith('/setmaster'):
        if not is_admin: await update.message.reply_text("❌ Admin only."); return
        context.user_data['step'] = 'master'; await update.message.reply_text("🔐 *Send MASTER SSID now:*", parse_mode='Markdown'); return
    if text.startswith('/myid'): await update.message.reply_text(f"Your ID: `{update.from_user.id}`", parse_mode='Markdown'); return
    if text.startswith('/users'):
        if not is_admin: await update.message.reply_text("❌ Admin only."); return
        users = load(USERS_FILE, {}); msg = f"👥 Total: {len(users)} | Copying: {sum(1 for u in users.values() if u.get('copying'))}\n\n"
        for k,v in list(users.items())[:20]: msg+=f"{v['license']} | {v['percent']}% | {'ON' if v['copying'] else 'OFF'}\n"
        await update.message.reply_text(msg); return

    if step == 'master':
        if not valid_ssid(text): await update.message.reply_text("❌ SSID too short.", reply_markup=back_kb()); return
        save(MASTER_FILE, {"ssid": text, "updated": datetime.now().timestamp()}); context.user_data['step']=None
        await update.message.reply_text("✅ *Master SSID Saved!*\n\nBot is now watching your trades. All users will auto copy.", reply_markup=main_kb(), parse_mode='Markdown'); return
    if step == 'license':
        licenses = load(LICENSES_FILE, {}); lic = text.upper()
        if lic not in licenses and not lic.startswith("TRADEXA-"): await update.message.reply_text("❌ Invalid license.", reply_markup=license_kb(), parse_mode='Markdown'); return
        if lic in licenses and licenses[lic].get('used') and licenses[lic].get('user_id') != uid: await update.message.reply_text("❌ License used by someone else.", reply_markup=license_kb()); return
        context.user_data['license']=lic; context.user_data['step']='ssid'
        await update.message.reply_text("✅ License OK!\n\n🔐 *STEP 2/3: Enter Broker SSID*", reply_markup=ssid_kb(), parse_mode='Markdown'); return
    if step == 'ssid':
        if not valid_ssid(text): await update.message.reply_text("❌ Invalid SSID.", reply_markup=ssid_kb()); return
        context.user_data['ssid']=text; context.user_data['step']='percent'
        await update.message.reply_text("✅ SSID OK!\n\n📊 *STEP 3/3: Copy %?*\n\nSend number 1-100\nEx: `50` for 50%", reply_markup=back_kb(), parse_mode='Markdown'); return
    if step == 'percent':
        try: p=int(text); assert 1<=p<=100
        except: await update.message.reply_text("❌ Send 1-100", reply_markup=back_kb()); return
        users = load(USERS_FILE, {}); licenses = load(LICENSES_FILE, {}); lic = context.user_data['license']
        if lic in licenses: days=licenses[lic].get('days',30); licenses[lic]['used']=True; licenses[lic]['user_id']=uid; licenses[lic]['activated']=datetime.now().timestamp(); licenses[lic]['expiry']=(datetime.now()+timedelta(days=days)).timestamp(); save(LICENSES_FILE, licenses); expiry_ts=licenses[lic]['expiry']; act_ts=licenses[lic]['activated']
        else: act_ts=datetime.now().timestamp(); expiry_ts=(datetime.now()+timedelta(days=30)).timestamp()
        users[uid]={"license": lic, "ssid": context.user_data['ssid'], "percent": p, "activated": act_ts, "expiry": expiry_ts, "copying": True, "username": update.from_user.username}; save(USERS_FILE, users); context.user_data.clear()
        await update.message.reply_text(f"🎉 *COPYING STARTED - {BOT_NAME}*\n\nLicense: `{lic}`\nCopy: {p}%\nExpires: {datetime.fromtimestamp(expiry_ts).strftime('%d/%m/%Y')}\n\n✅ Even if you go offline, trades will open!", reply_markup=main_kb(), parse_mode='Markdown'); return
    await start(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start)); app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
    app.add_handler(CommandHandler("genlicense", messages)); app.add_handler(CommandHandler("setmaster", messages))
    app.add_handler(CommandHandler("myid", messages)); app.add_handler(CommandHandler("users", messages))
    print("TRADEXA AI Running..."); app.run_polling()
if __name__ == "__main__": main()

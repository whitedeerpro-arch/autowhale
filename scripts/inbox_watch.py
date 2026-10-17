"""临时反射弧：轮询白名单私信，命中就用模板回一条（0 token）。

用法：python scripts/inbox_watch.py [--once] [--init]
状态：%USERPROFILE%\\.dsh\\bili-duty\\inbox-state.json
日志：%USERPROFILE%\\.dsh\\bili-duty\\inbox-watch.log
"""
import asyncio, json, os, sys
from datetime import datetime

from bilibili_api import session, Credential

HOME = os.path.join(os.path.expanduser("~"), ".dsh", "bili-duty")
CRED = os.path.join(HOME, "bili_credential.json")
STATE = os.path.join(HOME, "inbox-state.json")
LOG = os.path.join(HOME, "inbox-watch.log")
WHITELIST = {10450479}
ME = 569166300

c = json.load(open(CRED, encoding="utf-8"))
cred = Credential(sessdata=c["sessdata"], bili_jct=c["bili_jct"], buvid3=c.get("buvid3", ""), dedeuserid=c["dedeuserid"])


def log(msg):
    line = f"{datetime.now().isoformat(timespec='seconds')}  {msg}"
    print(line, flush=True)
    try:
        open(LOG, "a", encoding="utf-8").write(line + "\n")
    except Exception:
        pass


def txt(raw):
    try:
        j = json.loads(raw or "{}")
        return j.get("content") or j.get("title") or ""
    except Exception:
        return str(raw)[:120]


def canned(text):
    if any(k in text for k in ("在吗", "在么", "在不在")):
        return "在。本鲸在值班，有事直接说。"
    if any(k in text for k in ("唤起", "hihi", "hi", "你好", "hello")):
        return "在，被你叫起来了。有事直接说。"
    # 需要动脑的消息：别假装看懂了，先给一条诚实的占位
    if len(text) >= 12 or any(k in text for k in ("？", "?", "怎么", "为什么", "哪些", "如何", "帮我", "报错", "失败", "一下", "能不能")):
        return "收到。这条要动脑子，我处理完回你。"
    return "收到，本鲸看到了。"


def load_state():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {}


def save_state(s):
    open(STATE, "w", encoding="utf-8").write(json.dumps(s, ensure_ascii=False, indent=2))


async def tick(state, init=False):
    r = await session.get_sessions(cred)
    rows = r.get("session_list", []) if isinstance(r, dict) else []
    for s in rows:
        tid = s.get("talker_id")
        if tid not in WHITELIST:
            continue
        last = s.get("last_msg") or {}
        key = last.get("msg_key")
        if not key:
            continue
        # 最后一条是我自己发的（比如人工补答）→ 只更新游标，不重复回
        if init or last.get("sender_uid") == ME:
            state[str(tid)] = key
            continue
        if state.get(str(tid)) == key:
            continue
        # 有新消息：取最新一条来自对方的
        r2 = await session.fetch_session_msgs(credential=cred, talker_id=tid, session_type=1)
        msgs = r2.get("messages", []) if isinstance(r2, dict) else []
        inbound = next((m for m in msgs if m.get("sender_uid") != ME), None)
        if not inbound:
            state[str(tid)] = key
            continue
        text = txt(inbound.get("content"))
        reply = canned(text)
        try:
            out = await session.send_msg(credential=cred, receiver_id=tid, msg_type=session.EventType.TEXT, content=reply)
            state[str(tid)] = out.get("msg_key", key)
            log(f"reply -> {tid}: {reply}  (to: {text[:60]})")
        except Exception as e:
            state[str(tid)] = key
            log(f"send ERR {tid}: {type(e).__name__} {e}")
    save_state(state)


async def main():
    state = load_state()
    init = "--init" in sys.argv or not state
    if init:
        await tick(state, init=True)
        log("init state: " + json.dumps(state, ensure_ascii=False))
    if "--once" in sys.argv:
        await tick(state)
        return
    log("watching…")
    while True:
        try:
            await tick(state)
        except Exception as e:
            log(f"tick ERR {type(e).__name__} {e}")
        await asyncio.sleep(20)


asyncio.run(main())

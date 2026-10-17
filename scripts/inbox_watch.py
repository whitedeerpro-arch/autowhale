"""临时反射弧：轮询白名单私信，命中就用模板回一条（0 token）。

用法：python scripts/inbox_watch.py [--once] [--init]
状态：%USERPROFILE%\\.dsh\\bili-duty\\inbox-state.json
日志：%USERPROFILE%\\.dsh\\bili-duty\\inbox-watch.log
"""
import asyncio, json, os, sys, time, urllib.request
from datetime import datetime

from bilibili_api import session, Credential

HOME = os.path.join(os.path.expanduser("~"), ".dsh", "bili-duty")
CRED = os.path.join(HOME, "bili_credential.json")
STATE = os.path.join(HOME, "inbox-state.json")
LOG = os.path.join(HOME, "inbox-watch.log")
AGENT_LOG = os.path.join(HOME, "agent-spawn.log")
WHITELIST = {10450479}
ME = 569166300

# 高价值 → 让**宿主插件**代跑（宿主不受沙箱限制）
WEB_PORT_FILE = os.path.join(HOME, "web-port.txt")
SPAWN_PER_HOUR = 6
SPAWN_PER_DAY = 30

spawn_times = []


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


SPAM = ("抽奖", "互关", "广告", "点赞", "关注我", "加群", "刷单")


def classify(text):
    """浅过滤：只挡明显垃圾；熟人非寒暄就走模型。"""
    if any(k in text for k in SPAM):
        return None, False
    if any(k in text for k in ("在吗", "在么", "在不在")):
        return "在。本鲸在值班，有事直接说。", False
    if any(k in text for k in ("唤起", "hihi", "hi", "你好", "hello")):
        return "在，被你叫起来了。有事直接说。", False
    if len(text) >= 6 or any(k in text for k in ("？", "?", "怎么", "为什么", "哪些", "如何", "帮我", "报错", "失败", "一下", "能不能", "说说", "聊聊", "解释")):
        return "收到。这条要动脑子，我处理完回你。", True
    return "收到，本鲸看到了。", False


def spawn_agent(tid, text):
    """让宿主插件代跑一轮：POST /api/bili-duty/dm-reply（宿主不受沙箱限制）。"""
    now = time.time()
    spawn_times[:] = [t for t in spawn_times if now - t < 86400]
    if sum(1 for t in spawn_times if now - t < 3600) >= SPAWN_PER_HOUR:
        log("spawn skipped: hourly budget")
        return False
    if len(spawn_times) >= SPAWN_PER_DAY:
        log("spawn skipped: daily budget")
        return False
    try:
        port = int(open(WEB_PORT_FILE, encoding="utf-8").read().strip())
    except Exception:
        log("spawn skipped: web-port.txt missing (插件没重启？)")
        return False
    body = json.dumps({"tid": tid, "text": text}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/bili-duty/dm-reply",
        data=body, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("busy") or data.get("started") is False:
            log(f"spawn skipped: host busy/rejected {json.dumps(data, ensure_ascii=False)}")
            return False
        spawn_times.append(now)
        log(f"spawn agent via host for {tid} (24h {len(spawn_times)})")
        return True
    except Exception as e:
        log(f"spawn ERR {type(e).__name__}: {e}")
        return False


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
        reply, want_agent = classify(text)
        if reply:
            try:
                out = await session.send_msg(credential=cred, receiver_id=tid, msg_type=session.EventType.TEXT, content=reply)
                state[str(tid)] = out.get("msg_key", key)
                log(f"reply -> {tid}: {reply}  (to: {text[:60]})")
            except Exception as e:
                state[str(tid)] = key
                log(f"send ERR {tid}: {type(e).__name__} {e}")
        else:
            state[str(tid)] = key
            log(f"ignore -> {tid}: {text[:60]}")
        if want_agent:
            spawn_agent(tid, text)
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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except BaseException:
        import traceback
        log("FATAL\n" + traceback.format_exc())


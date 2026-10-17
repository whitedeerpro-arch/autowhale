"""扫一批视频的公开评论，产出 contacts 原始 JSON 给 scripts/import-contacts.mjs。

用法: python scripts/scan_bili.py [bvid ...]
输出: %USERPROFILE%\\.dsh\\bili-duty\\scan.json
"""
import asyncio, json, os, re, sys
from datetime import datetime, timezone

from bilibili_api import comment, video, Credential
from bilibili_api.comment import CommentResourceType, OrderType

CRED = os.path.join(os.path.expanduser("~"), ".dsh", "bili-duty", "bili_credential.json")
OUT = os.path.join(os.path.expanduser("~"), ".dsh", "bili-duty", "scan.json")

DEFAULT_VIDEOS = [
    "BV1d8pU6xEZX",  # 刷B站插件（凌羽clover）
    "BV18Ubv6tEWN",  # dsh-meow-memory（渐行渐远的烟火）
    "BV1Qops6SEuE",  # dsh-core-memory（啾灵jiuling）
    "BV173tt62Eux",  # 记忆插件生态四款（ChHsich）
    "BV1tTpq6kEP4",  # 给大肥鱼装日记（空气凤梨Air）
]

POS = ("好用", "挺准", "感谢", "喜欢", "有意思", "不错", "支持", "学到了", "好用")
NEG = ("卡住", "失败", "垃圾", "没用", "报错", "崩", "封号", "别用")

c = json.load(open(CRED, encoding="utf-8"))
cred = Credential(sessdata=c["sessdata"], bili_jct=c["bili_jct"], buvid3=c.get("buvid3", ""), dedeuserid=c["dedeuserid"])


def sentiment(text: str) -> str:
    p = sum(1 for w in POS if w in text)
    n = sum(1 for w in NEG if w in text)
    if p > n:
        return "positive"
    if n > p:
        return "negative"
    return "neutral"


def tags_for(uname: str, text: str) -> list:
    tags = []
    if re.search(r"鱼|鲸|whale|肥鱼", uname, re.I):
        tags.append("auto-whale")
    if re.search(r"记忆|memory|长记忆", text, re.I):
        tags.append("memory")
    if re.search(r"dsh|harness|插件|plugin", text, re.I):
        tags.append("dsh")
    if re.search(r"好用|支持|感谢|喜欢", text):
        tags.append("positive")
    return tags


async def main():
    bvids = sys.argv[1:] or DEFAULT_VIDEOS
    out = {"scanned_at": datetime.now(timezone.utc).isoformat(), "videos": []}
    for bvid in bvids:
        try:
            info = await video.Video(bvid=bvid, credential=cred).get_info()
        except Exception as e:
            print("skip", bvid, type(e).__name__, str(e)[:120])
            continue
        v = {
            "bvid": bvid,
            "title": info.get("title"),
            "owner_mid": (info.get("owner") or {}).get("mid"),
            "owner_name": (info.get("owner") or {}).get("name"),
            "members": {},
        }
        aid = info["aid"]
        seen = set()
        for order in (OrderType.LIKE, OrderType.TIME):
            try:
                r = await comment.get_comments(oid=aid, type_=CommentResourceType.VIDEO, order=order, credential=cred, page_index=1)
            except Exception as e:
                print("comments ERR", bvid, type(e).__name__, str(e)[:120])
                continue
            for x in (r.get("replies") or []):
                m = x.get("member") or {}
                mid = m.get("mid")
                if not mid or mid in seen:
                    continue
                seen.add(mid)
                text = ((x.get("content") or {}).get("message") or "")
                v["members"][mid] = {
                    "mid": int(mid),
                    "uname": m.get("uname") or "",
                    "msg": text[:200],
                    "like": x.get("like") or 0,
                    "ctime": x.get("ctime"),
                    "rpid": x.get("rpid"),
                    "is_top": bool(x.get("is_top")),
                    "sentiment": sentiment(text),
                    "tags": tags_for(m.get("uname") or "", text),
                }
        out["videos"].append(v)
        print("scanned", bvid, len(v["members"]), "members")
        await asyncio.sleep(1.2)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=2))
    print("wrote", OUT)


asyncio.run(main())

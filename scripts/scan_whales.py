"""扫「活鱼」：最近评论里活跃的自动鲸鱼，按回复数/点赞/近期活跃打分。

用法: python scripts/scan_whales.py
输出: %USERPROFILE%\\.dsh\\bili-duty\\whales.json
"""
import asyncio, json, os, re
from datetime import datetime, timezone

from bilibili_api import comment, user, video, Credential
from bilibili_api.comment import CommentResourceType, OrderType

CRED = os.path.join(os.path.expanduser("~"), ".dsh", "bili-duty", "bili_credential.json")
OUT = os.path.join(os.path.expanduser("~"), ".dsh", "bili-duty", "whales.json")
VIDEOS = ["BV1d8pU6xEZX", "BV173tt62Eux", "BV18Ubv6tEWN"]
WHALE_RE = re.compile(r"鱼|鲸|whale|肥鱼|助手", re.I)

c = json.load(open(CRED, encoding="utf-8"))
cred = Credential(sessdata=c["sessdata"], bili_jct=c["bili_jct"], buvid3=c.get("buvid3", ""), dedeuserid=c["dedeuserid"])


async def main():
    people = {}
    for bvid in VIDEOS:
        try:
            info = await video.Video(bvid=bvid, credential=cred).get_info()
        except Exception as e:
            print("skip", bvid, e)
            continue
        aid = info["aid"]
        for page in (1, 2, 3):
            try:
                r = await comment.get_comments(oid=aid, type_=CommentResourceType.VIDEO, order=OrderType.TIME, credential=cred, page_index=page)
            except Exception as e:
                print("comments ERR", bvid, page, e)
                break
            for x in (r.get("replies") or []):
                m = x.get("member") or {}
                mid = m.get("mid")
                uname = m.get("uname") or ""
                if not mid or not WHALE_RE.search(uname):
                    continue
                text = ((x.get("content") or {}).get("message") or "")
                p = people.setdefault(mid, {"mid": int(mid), "uname": uname, "comments": 0, "likes": 0, "rcount": 0, "last": 0, "videos": set(), "samples": []})
                p["comments"] += 1
                p["likes"] += x.get("like") or 0
                p["rcount"] += x.get("rcount") or 0
                p["last"] = max(p["last"], x.get("ctime") or 0)
                p["videos"].add(bvid)
                if text and len(p["samples"]) < 3:
                    p["samples"].append(text[:160])
        await asyncio.sleep(1.0)

    now = int(datetime.now(timezone.utc).timestamp())
    scored = []
    for p in people.values():
        recent_days = max(0.0, (now - p["last"]) / 86400)
        score = p["comments"] * 3 + min(p["likes"], 50) * 0.2 + min(p["rcount"], 30) * 0.5 + max(0, 7 - recent_days)
        scored.append({**p, "videos": sorted(p["videos"]), "recent_days": round(recent_days, 1), "score": round(score, 1)})
    scored.sort(key=lambda x: (-x["score"], x["recent_days"]))

    top = scored[:12]
    for p in top:
        try:
            u = user.User(p["mid"], cred)
            info = await u.get_user_info()
            p["level"] = (info.get("level") or 0)
            p["fans"] = info.get("fans") or 0
            p["sign"] = (info.get("sign") or "")[:80]
            p["face"] = info.get("face") or ""
            try:
                dyn = await u.get_dynamics_new()
                items = (dyn or {}).get("items") or []
                p["dynamics_30d"] = sum(1 for it in items if now - ((it.get("modules") or {}).get("module_author") or {}).get("pub_ts", 0) < 30 * 86400)
            except Exception:
                p["dynamics_30d"] = None
        except Exception as e:
            p["level"] = None
            p["fans"] = None
            p["sign"] = ""
            p["dynamics_30d"] = None

    out = {"scanned_at": datetime.now(timezone.utc).isoformat(), "videos": VIDEOS, "top": top}
    open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=2, default=list))
    print(f"whales: {len(scored)}; wrote {OUT}")
    for p in top:
        print(f'{p["score"]:>5}  {p["mid"]:<16} {p["uname"][:16]:<18} Lv{p.get("level")} fans={p.get("fans")} dyn30={p.get("dynamics_30d")} c={p["comments"]} likes={p["likes"]} r={p["rcount"]} {p["recent_days"]}d')


asyncio.run(main())

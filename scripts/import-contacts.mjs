// 把 scan.json 导入本机通讯录：node scripts/import-contacts.mjs
import { DatabaseSync } from 'node:sqlite'
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { homedir } from 'node:os'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const scanFile = join(homedir(), '.dsh', 'bili-duty', 'scan.json')
if (!existsSync(scanFile)) {
  console.error('missing', scanFile)
  process.exit(1)
}
const scan = JSON.parse(readFileSync(scanFile, 'utf8'))
const db = new DatabaseSync(join(root, 'data', 'autowhale.db'))
const now = new Date().toISOString().slice(0, 10)

const roleRank = { observer: 0, commenter: 1, inbound: 2, up: 3, self: 4 }
const SELF_MID = 569166300
const get = db.prepare('SELECT * FROM contacts WHERE mid = ?')
const insert = db.prepare(`INSERT INTO contacts (mid, uname, role, tags, sentiment, relation, notes, first_seen, last_seen, observations)
  VALUES (?, ?, ?, ?, ?, 'none', ?, ?, ?, 1)`)
const update = db.prepare(`UPDATE contacts SET uname=?, role=?, tags=?, sentiment=?, notes=?, last_seen=?, observations=? WHERE mid=?`)
const event = db.prepare('INSERT INTO contact_events (mid, ts, kind, bvid, rpid, summary) VALUES (?,?,?,?,?,?)')
const seenEvent = db.prepare("SELECT 1 FROM contact_events WHERE mid=? AND kind='observed' AND bvid=? AND COALESCE(rpid,'')=COALESCE(?,'')")

const tagSet = (s) => new Set(String(s || '').split(',').map((x) => x.trim()).filter(Boolean))
const roleOf = (a, b) => (roleRank[a] >= roleRank[b] ? a : b)

let added = 0
for (const v of scan.videos) {
  const vidTags = ['dsh']
  if (/插件|刷B站/.test(v.title || '')) vidTags.push('plugin-author')
  if (/记忆|memory/i.test(v.title || '')) vidTags.push('memory')
  const people = []
  if (v.owner_mid) {
    people.push({ mid: v.owner_mid, uname: v.owner_name, role: 'up', tags: vidTags, sentiment: 'positive', notes: `UP：${v.title}`.slice(0, 160), bvid: v.bvid, rpid: null, summary: `UP：${v.title}`.slice(0, 160) })
  }
  for (const m of Object.values(v.members || {})) {
    const role = (m.tags || []).includes('auto-whale') ? 'commenter' : 'observer'
    people.push({ mid: m.mid, uname: m.uname, role, tags: m.tags || [], sentiment: m.sentiment, notes: (m.msg || '').slice(0, 160), bvid: v.bvid, rpid: m.rpid, summary: (m.msg || '').slice(0, 160) })
  }
  for (const p of people) {
    if (p.mid === SELF_MID) continue
    if (seenEvent.get(p.mid, p.bvid, p.rpid == null ? null : String(p.rpid))) continue
    const cur = get.get(p.mid)
    if (!cur) {
      insert.run(p.mid, p.uname || '', p.role, (p.tags || []).join(','), p.sentiment || 'unknown', p.notes || '', now, now)
      added++
    } else {
      const tags = tagSet(cur.tags)
      for (const t of p.tags || []) tags.add(t)
      update.run(p.uname || cur.uname, roleOf(cur.role, p.role), [...tags].join(','), p.sentiment || cur.sentiment, p.notes || cur.notes, now, (cur.observations || 0) + 1, p.mid)
    }
    event.run(p.mid, now, 'observed', p.bvid, p.rpid == null ? null : String(p.rpid), p.summary || '')
  }
}

const rows = db.prepare(`SELECT mid, uname, role, tags, sentiment, observations, outbound_count FROM contacts
  ORDER BY CASE role WHEN 'up' THEN 0 WHEN 'inbound' THEN 1 WHEN 'commenter' THEN 2 ELSE 3 END,
           observations DESC, last_seen DESC LIMIT 25`).all()

const lines = ['# 通讯录（本地生成，公开信息）', '', `> 扫描于 ${scan.scanned_at}；只记 B站 公开可见信息`, '', '| mid | 昵称 | 角色 | 标签 | 情绪 | 观察次数 | 已发信 |', '|---|---|---|---|---|---|---|']
for (const r of rows) lines.push(`| ${r.mid} | ${r.uname} | ${r.role} | ${r.tags} | ${r.sentiment} | ${r.observations} | ${r.outbound_count} |`)
writeFileSync(join(root, 'data', 'contacts.md'), lines.join('\n') + '\n')

console.log(`imported ${added} new contacts; total ${db.prepare('SELECT COUNT(*) AS n FROM contacts').get().n}`)
for (const r of rows.slice(0, 15)) console.log(`${r.role.padEnd(9)} ${String(r.mid).padEnd(12)} ${r.uname}  [${r.tags}] x${r.observations}`)
db.close()

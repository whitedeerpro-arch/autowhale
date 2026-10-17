// 记一次主动发信：node scripts/log-outbound.mjs <mid> "<摘要>"
// 会更新 contacts 的发信次数、最后发信时间、7 天冷却，并写 contact_events。
import { DatabaseSync } from 'node:sqlite'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const [, , midArg, ...rest] = process.argv
const mid = Number(midArg)
const summary = rest.join(' ')
if (!mid || !summary) {
  console.error('usage: node scripts/log-outbound.mjs <mid> "<summary>"')
  process.exit(2)
}

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const db = new DatabaseSync(join(root, 'data', 'autowhale.db'))
const now = new Date()
const ts = now.toISOString()
const cooldown = new Date(now.getTime() + 7 * 86400_000).toISOString()
const today = ts.slice(0, 10)

const cur = db.prepare('SELECT * FROM contacts WHERE mid = ?').get(mid)
if (!cur) {
  db.prepare(`INSERT INTO contacts (mid, uname, role, tags, sentiment, relation, notes, first_seen, last_seen, observations)
    VALUES (?, ?, 'observer', 'outbound', 'unknown', 'none', '', ?, ?, 0)`).run(mid, `mid:${mid}`, today, today)
}
db.prepare('INSERT INTO contact_events (mid, ts, kind, summary) VALUES (?,?,?,?)').run(mid, ts, 'outbound', summary)
db.prepare(`UPDATE contacts SET outbound_count = outbound_count + 1, last_outbound_at = ?, cooldown_until = ?, last_seen = ? WHERE mid = ?`)
  .run(ts, cooldown, today, mid)

const out = db.prepare('SELECT mid, uname, outbound_count, last_outbound_at, cooldown_until FROM contacts WHERE mid = ?').get(mid)
console.log('logged outbound:', JSON.stringify(out))
db.close()

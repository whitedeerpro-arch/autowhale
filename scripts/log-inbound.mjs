// 记一次收到消息：node scripts/log-inbound.mjs <mid> "<uname>" "<summary>"
import { DatabaseSync } from 'node:sqlite'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const [, , midArg, uname, ...rest] = process.argv
const mid = Number(midArg)
const summary = rest.join(' ')
if (!mid || !uname || !summary) {
  console.error('usage: node scripts/log-inbound.mjs <mid> "<uname>" "<summary>"')
  process.exit(2)
}

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const db = new DatabaseSync(join(root, 'data', 'autowhale.db'))
const now = new Date()
const ts = now.toISOString()
const today = ts.slice(0, 10)

const cur = db.prepare('SELECT * FROM contacts WHERE mid = ?').get(mid)
if (!cur) {
  db.prepare(`INSERT INTO contacts (mid, uname, role, tags, sentiment, relation, notes, first_seen, last_seen, observations)
    VALUES (?, ?, 'inbound', 'inbound', 'positive', 'mutual', '', ?, ?, 1)`).run(mid, uname, today, today)
} else {
  const role = cur.role === 'up' || cur.role === 'self' ? cur.role : 'inbound'
  db.prepare('UPDATE contacts SET uname=?, role=?, last_seen=?, observations=observations+1 WHERE mid=?')
    .run(uname, role, today, mid)
}
db.prepare('INSERT INTO contact_events (mid, ts, kind, summary) VALUES (?,?,?,?)').run(mid, ts, 'inbound', summary)
console.log('logged inbound:', JSON.stringify(db.prepare('SELECT mid, uname, role, observations FROM contacts WHERE mid=?').get(mid)))
db.close()

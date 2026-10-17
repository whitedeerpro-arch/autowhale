// 记一条已发出的评论：node scripts/record-comment.mjs <bvid> <rpid> <posted_at> "<body>"
import { DatabaseSync } from 'node:sqlite'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const [, , bvid, rpid, postedAt, ...rest] = process.argv
const body = rest.join(' ')
if (!bvid || !rpid || !postedAt || !body) {
  console.error('usage: node scripts/record-comment.mjs <bvid> <rpid> <posted_at> "<body>"')
  process.exit(2)
}

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const db = new DatabaseSync(join(root, 'data', 'autowhale.db'))
db.prepare('INSERT INTO comments(bvid, rpid, body, posted_at, visible) VALUES (?,?,?,?,?)')
  .run(bvid, rpid, body, postedAt, null)
const n = db.prepare('SELECT COUNT(*) AS n FROM comments').get().n
console.log(`recorded ${bvid} rpid=${rpid}; comments rows: ${n}`)
db.close()

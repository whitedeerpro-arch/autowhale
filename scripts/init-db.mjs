// 初始化本地库：node scripts/init-db.mjs
// 需要 Node >= 22.5（用内置 node:sqlite；DSH 自带的 Node 24 就行）
import { DatabaseSync } from 'node:sqlite'
import { mkdirSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const dbFile = join(root, 'data', 'autowhale.db')
mkdirSync(dirname(dbFile), { recursive: true })

const db = new DatabaseSync(dbFile)
db.exec(readFileSync(join(root, 'db', 'schema.sql'), 'utf8'))

const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").all()
console.log('db:', dbFile)
console.log('tables:', tables.map((t) => t.name).join(', '))
for (const t of tables) {
  const n = db.prepare(`SELECT COUNT(*) AS n FROM "${t.name}"`).get()
  console.log(`  ${t.name}: ${n.n}`)
}
db.close()

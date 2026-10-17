// 预制回复匹配（宿主侧、0 token）：node scripts/match-reply.mjs "在吗"
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const cfg = JSON.parse(readFileSync(join(root, 'config', 'replies.json'), 'utf8'))
const text = process.argv.slice(2).join(' ').trim()
if (!text) {
  console.error('usage: node scripts/match-reply.mjs "<message>"')
  process.exit(2)
}

function hit(rule) {
  const list = Array.isArray(rule.match) ? rule.match : [rule.match]
  for (const m of list) {
    if (rule.type === 'exact' && text === m) return m
    if (rule.type === 'contains' && text.includes(m)) return m
    if (rule.type === 'regex' && new RegExp(m).test(text)) return m
  }
  return null
}

let matched = null
for (const rule of cfg.rules || []) {
  const m = hit(rule)
  if (m) { matched = { id: rule.id, matched: m, action: rule.action || 'reply', reply: rule.reply || cfg.fallback || '' }; break }
}
console.log(JSON.stringify(matched || { id: 'none', action: cfg.fallback ? 'reply' : 'log', reply: cfg.fallback || '' }, null, 2))

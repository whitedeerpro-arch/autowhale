// 价值分闸门：node scripts/score-message.mjs --from 10450479 "帮我看看这个报错"
// 先跑预制回复；没命中再打分；分数过线才建议叫醒模型。
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const gate = JSON.parse(readFileSync(join(root, 'config', 'gate.json'), 'utf8'))
const replies = JSON.parse(readFileSync(join(root, 'config', 'replies.json'), 'utf8'))

const args = process.argv.slice(2)
let from = 0
const words = []
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--from') { from = Number(args[++i]) || 0 } else words.push(args[i])
}
const text = words.join(' ').trim()
if (!text) {
  console.error('usage: node scripts/score-message.mjs --from <mid> "<message>"')
  process.exit(2)
}

function canned(t) {
  for (const rule of replies.rules || []) {
    const list = Array.isArray(rule.match) ? rule.match : [rule.match]
    for (const m of list) {
      if (rule.type === 'exact' && t === m) return rule
      if (rule.type === 'contains' && t.includes(m)) return rule
      if (rule.type === 'regex' && new RegExp(m).test(t)) return rule
    }
  }
  return null
}

const w = gate.weights
const reasons = []
let score = 0

if (gate.blocklist.includes(from)) { reasons.push('blocklist'); score = -99 }
if (from === gate.owner) { score += w.owner; reasons.push(`owner +${w.owner}`) }
else if (gate.whitelist.includes(from)) { score += w.whitelist; reasons.push(`whitelist +${w.whitelist}`) }

if (/[?？]/.test(text) || /(吗|呢|怎么|为什么|如何|能不能)/.test(text)) { score += w.question; reasons.push(`question +${w.question}`) }
if (gate.taskWords.some((x) => text.includes(x))) { score += w.task; reasons.push(`task +${w.task}`) }
if (/(BV[0-9A-Za-z]{10}|https?:\/\/|\d{2,}|报错|异常|日志|token)/i.test(text)) { score += w.specific; reasons.push(`specific +${w.specific}`) }
if (text.length >= 30) { score += w.long; reasons.push(`long +${w.long}`) }
if (text.length <= 3 && !/[?？]/.test(text)) { score += w.short; reasons.push(`short ${w.short}`) }
if (gate.spamWords.some((x) => text.includes(x))) { score += w.spam; reasons.push(`spam ${w.spam}`) }

const c = canned(text)
const trusted = from === gate.owner || gate.whitelist.includes(from)
let decision
if (c?.action === 'ignore') decision = 'ignore'
else if (c?.action === 'status') decision = 'status'
else if (c?.reply) decision = 'canned'
else if (c?.action === 'llm' && (trusted || score >= gate.thresholds.llm)) decision = 'llm'
else if (score >= gate.thresholds.llm) decision = 'llm'
else if (score >= gate.thresholds.template && gate.templateWhenLowValue) decision = 'template'
else decision = 'ignore'

console.log(JSON.stringify({
  from, text, score, reasons,
  canned: c ? c.id : null,
  decision,
  reply: c?.reply || (decision === 'template' ? gate.templateWhenLowValue : ''),
}, null, 2))

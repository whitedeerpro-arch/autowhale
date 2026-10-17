-- autowhale 本地库 · schema v1
-- 用 node:sqlite / Python sqlite3 都能开；WAL 模式，单文件。
-- 位置：data/autowhale.db（不进仓库）

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- 每轮：谁触发的、跑了多久、花了多少
CREATE TABLE IF NOT EXISTS rounds (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at  TEXT    NOT NULL,
  ended_at    TEXT,
  trigger     TEXT    NOT NULL DEFAULT 'manual',  -- manual / noon / night
  exit_code   INTEGER,
  picked      INTEGER NOT NULL DEFAULT 0,
  report_path TEXT,
  note        TEXT    NOT NULL DEFAULT ''
);

-- 看过的视频：判重表的真相来源
CREATE TABLE IF NOT EXISTS videos (
  bvid       TEXT    PRIMARY KEY,
  title      TEXT    NOT NULL DEFAULT '',
  up_name    TEXT    NOT NULL DEFAULT '',
  up_mid     INTEGER,
  pubdate    INTEGER,
  duration   INTEGER,
  first_seen TEXT    NOT NULL,
  last_seen  TEXT    NOT NULL,
  status     TEXT    NOT NULL DEFAULT 'seen',     -- seen / picked / skipped / commented
  reason     TEXT    NOT NULL DEFAULT '',
  round_id   INTEGER REFERENCES rounds(id)
);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_last_seen ON videos(last_seen);

-- 我发出去的评论（含复核结果）
CREATE TABLE IF NOT EXISTS comments (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  bvid        TEXT    NOT NULL,
  rpid        TEXT,
  root_rpid   TEXT,
  body        TEXT    NOT NULL DEFAULT '',
  posted_at   TEXT    NOT NULL,
  verified_at TEXT,
  visible     INTEGER,                            -- 1 可见 / 0 没查到 / NULL 未核
  round_id    INTEGER REFERENCES rounds(id)
);
CREATE INDEX IF NOT EXISTS idx_comments_bvid ON comments(bvid);

-- 字幕 / 转写原文（判断依据，不再只留在报告里）
CREATE TABLE IF NOT EXISTS transcripts (
  bvid       TEXT    NOT NULL,
  source     TEXT    NOT NULL,                    -- cc / asr
  lang       TEXT    NOT NULL DEFAULT '',
  text       TEXT    NOT NULL DEFAULT '',
  fetched_at TEXT    NOT NULL,
  PRIMARY KEY (bvid, source)
);

-- 审计：配置变更、登录、异常
CREATE TABLE IF NOT EXISTS events (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  ts      TEXT    NOT NULL,
  kind    TEXT    NOT NULL,
  payload TEXT    NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);

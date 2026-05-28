CREATE TABLE IF NOT EXISTS events (
    id           INTEGER PRIMARY KEY,
    timestamp    TIMESTAMP NOT NULL,
    source       TEXT NOT NULL,
    event_type   TEXT NOT NULL,
    metadata     JSON NOT NULL,
    embedding_id TEXT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(timestamp, source, event_type)
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(source, event_type);

CREATE TABLE IF NOT EXISTS habits (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    color      TEXT NOT NULL DEFAULT '#6b9e6b',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ideas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    text        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'active',
    repo        TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL DEFAULT 'New Chat',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL,
    sources     JSON NOT NULL DEFAULT '[]',
    text        TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS whatsapp_chats (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_name     TEXT NOT NULL UNIQUE,
    file_name     TEXT NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0,
    participants  TEXT NOT NULL DEFAULT '[]',
    date_from     TEXT,
    date_to       TEXT,
    ingested_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS whatsapp_messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_name  TEXT NOT NULL REFERENCES whatsapp_chats(chat_name) ON DELETE CASCADE,
    timestamp  TEXT NOT NULL,
    sender     TEXT NOT NULL,
    message    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_wa_messages_chat ON whatsapp_messages(chat_name);
CREATE INDEX IF NOT EXISTS idx_wa_messages_ts   ON whatsapp_messages(timestamp);

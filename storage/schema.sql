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

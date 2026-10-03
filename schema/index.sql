PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;
PRAGMA wal_autocheckpoint=1000;
PRAGMA temp_store=MEMORY;
PRAGMA trusted_schema=OFF;

CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at_ns INTEGER NOT NULL,
  build_id TEXT NOT NULL
);

CREATE VIRTUAL TABLE memory_fts USING fts5(
  identity UNINDEXED,
  kind UNINDEXED,
  text,
  tokenize='unicode61 remove_diacritics 2'
);

CREATE TABLE embedding_models (
  model_id BLOB PRIMARY KEY CHECK(length(model_id)=16),
  dimension INTEGER NOT NULL CHECK(dimension > 0),
  metric TEXT NOT NULL CHECK(metric IN ('cosine')),
  created_at_ns INTEGER NOT NULL
);

CREATE TABLE embeddings (
  model_id BLOB NOT NULL REFERENCES embedding_models(model_id),
  identity BLOB NOT NULL CHECK(length(identity)=16),
  vector_f32le BLOB NOT NULL,
  source_revision INTEGER NOT NULL,
  PRIMARY KEY(model_id, identity)
) WITHOUT ROWID;

CREATE INDEX embeddings_identity ON embeddings(identity, model_id);

CREATE TABLE retrieval_stats (
  identity BLOB PRIMARY KEY CHECK(length(identity)=16),
  recalled_count INTEGER NOT NULL DEFAULT 0,
  selected_count INTEGER NOT NULL DEFAULT 0,
  useful_count INTEGER NOT NULL DEFAULT 0,
  last_recalled_at_ns INTEGER NULL
);

PRAGMA user_version=1;

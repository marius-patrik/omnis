PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;
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

CREATE TABLE graph_meta (
  singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
  revision INTEGER NOT NULL CHECK (revision >= 0)
);
INSERT INTO graph_meta(singleton, revision) VALUES (1, 0);

CREATE TABLE provenance (
  id BLOB PRIMARY KEY CHECK(length(id)=16),
  source TEXT NOT NULL,
  method TEXT NOT NULL,
  version TEXT NOT NULL DEFAULT '',
  confidence REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
  created_at_ns INTEGER NOT NULL
);

CREATE TABLE provenance_evidence (
  provenance_id BLOB NOT NULL REFERENCES provenance(id),
  ordinal INTEGER NOT NULL,
  artifact_id BLOB NOT NULL CHECK(length(artifact_id)=32),
  PRIMARY KEY(provenance_id, ordinal)
) WITHOUT ROWID;

CREATE TABLE nodes (
  id BLOB PRIMARY KEY CHECK(length(id)=16),
  created_revision INTEGER NOT NULL CHECK(created_revision > 0),
  deleted_revision INTEGER NULL,
  CHECK(deleted_revision IS NULL OR deleted_revision > created_revision)
);

CREATE TABLE node_kinds (
  node_id BLOB NOT NULL REFERENCES nodes(id),
  kind TEXT NOT NULL,
  authority TEXT NOT NULL,
  valid_from_revision INTEGER NOT NULL,
  valid_to_revision INTEGER NULL,
  PRIMARY KEY(node_id, kind, valid_from_revision)
) WITHOUT ROWID;

CREATE INDEX node_kinds_current_kind
ON node_kinds(kind, node_id)
WHERE valid_to_revision IS NULL;

CREATE TABLE node_properties (
  node_id BLOB NOT NULL REFERENCES nodes(id),
  namespace TEXT NOT NULL,
  key TEXT NOT NULL,
  value_type INTEGER NOT NULL,
  value BLOB NOT NULL,
  authority TEXT NOT NULL,
  provenance_id BLOB NULL REFERENCES provenance(id),
  valid_from_revision INTEGER NOT NULL,
  valid_to_revision INTEGER NULL,
  PRIMARY KEY(node_id, namespace, key, valid_from_revision)
) WITHOUT ROWID;

CREATE INDEX node_properties_current_key
ON node_properties(namespace, key, node_id)
WHERE valid_to_revision IS NULL;

CREATE TABLE edges (
  id BLOB PRIMARY KEY CHECK(length(id)=16),
  source BLOB NOT NULL REFERENCES nodes(id),
  relation TEXT NOT NULL,
  target BLOB NOT NULL REFERENCES nodes(id),
  dimension TEXT NOT NULL,
  authority TEXT NOT NULL,
  provenance_id BLOB NULL REFERENCES provenance(id),
  valid_from_revision INTEGER NOT NULL,
  valid_to_revision INTEGER NULL
);

CREATE INDEX edges_current_out
ON edges(source, relation, target, id)
WHERE valid_to_revision IS NULL;

CREATE INDEX edges_current_in
ON edges(target, relation, source, id)
WHERE valid_to_revision IS NULL;

CREATE INDEX edges_current_dimension
ON edges(dimension, source, target, id)
WHERE valid_to_revision IS NULL;

CREATE TABLE edge_properties (
  edge_id BLOB NOT NULL REFERENCES edges(id),
  namespace TEXT NOT NULL,
  key TEXT NOT NULL,
  value_type INTEGER NOT NULL,
  value BLOB NOT NULL,
  authority TEXT NOT NULL,
  provenance_id BLOB NULL REFERENCES provenance(id),
  valid_from_revision INTEGER NOT NULL,
  valid_to_revision INTEGER NULL,
  PRIMARY KEY(edge_id, namespace, key, valid_from_revision)
) WITHOUT ROWID;

CREATE TABLE aliases (
  namespace TEXT NOT NULL,
  alias TEXT NOT NULL,
  node_id BLOB NOT NULL REFERENCES nodes(id),
  authority TEXT NOT NULL,
  valid_from_revision INTEGER NOT NULL,
  valid_to_revision INTEGER NULL,
  PRIMARY KEY(namespace, alias, node_id, valid_from_revision)
) WITHOUT ROWID;

CREATE INDEX aliases_current_exact
ON aliases(namespace, alias, node_id)
WHERE valid_to_revision IS NULL;

CREATE TABLE transactions (
  id BLOB PRIMARY KEY CHECK(length(id)=16),
  actor BLOB NOT NULL CHECK(length(actor)=16),
  authority TEXT NOT NULL,
  trace_id BLOB NOT NULL CHECK(length(trace_id)=16),
  previous_revision INTEGER NOT NULL,
  new_revision INTEGER NOT NULL UNIQUE,
  committed_at_ns INTEGER NOT NULL,
  mutation_count INTEGER NOT NULL,
  CHECK(new_revision = previous_revision + 1)
);

CREATE TABLE transaction_causes (
  transaction_id BLOB NOT NULL REFERENCES transactions(id),
  event_id BLOB NOT NULL CHECK(length(event_id)=16),
  PRIMARY KEY(transaction_id, event_id)
) WITHOUT ROWID;

CREATE TABLE outbox_events (
  ingest_seq INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id BLOB NOT NULL UNIQUE CHECK(length(event_id)=16),
  event_type TEXT NOT NULL,
  envelope BLOB NOT NULL,
  created_at_ns INTEGER NOT NULL,
  acked_at_ns INTEGER NULL
);

CREATE INDEX outbox_pending
ON outbox_events(ingest_seq)
WHERE acked_at_ns IS NULL;

CREATE TABLE artifact_meta (
  artifact_id BLOB PRIMARY KEY CHECK(length(artifact_id)=32),
  length INTEGER NOT NULL CHECK(length >= 0),
  media_type TEXT NOT NULL,
  protection_class INTEGER NOT NULL,
  creator BLOB NOT NULL CHECK(length(creator)=16),
  created_at_ns INTEGER NOT NULL,
  tombstoned_at_ns INTEGER NULL
);

CREATE TABLE artifact_refs (
  owner_kind TEXT NOT NULL,
  owner_id BLOB NOT NULL,
  role TEXT NOT NULL,
  artifact_id BLOB NOT NULL REFERENCES artifact_meta(artifact_id),
  PRIMARY KEY(owner_kind, owner_id, role, artifact_id)
) WITHOUT ROWID;

PRAGMA user_version=1;

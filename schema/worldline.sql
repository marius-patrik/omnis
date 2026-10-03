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

CREATE TABLE events (
  id BLOB PRIMARY KEY CHECK(length(id)=16),
  ingest_seq INTEGER NOT NULL UNIQUE CHECK(ingest_seq > 0),
  type TEXT NOT NULL,
  schema_major INTEGER NOT NULL,
  schema_minor INTEGER NOT NULL,
  source BLOB NOT NULL CHECK(length(source)=16),
  actor BLOB NOT NULL CHECK(length(actor)=16),
  observed_wall_ns INTEGER NOT NULL,
  observed_monotonic_ns INTEGER NOT NULL,
  graph_revision INTEGER NULL,
  trace_id BLOB NOT NULL CHECK(length(trace_id)=16),
  envelope BLOB NOT NULL,
  erased INTEGER NOT NULL DEFAULT 0 CHECK(erased IN (0,1))
);

CREATE TABLE event_causes (
  event_id BLOB NOT NULL REFERENCES events(id),
  ordinal INTEGER NOT NULL,
  parent_event_id BLOB NOT NULL CHECK(length(parent_event_id)=16),
  PRIMARY KEY(event_id, ordinal),
  UNIQUE(event_id, parent_event_id)
) WITHOUT ROWID;

CREATE INDEX event_causes_parent
ON event_causes(parent_event_id, event_id);

CREATE TABLE event_entities (
  event_id BLOB NOT NULL REFERENCES events(id),
  ordinal INTEGER NOT NULL,
  node_id BLOB NOT NULL CHECK(length(node_id)=16),
  role TEXT NOT NULL,
  PRIMARY KEY(event_id, ordinal)
) WITHOUT ROWID;

CREATE INDEX event_entities_node
ON event_entities(node_id, event_id);

CREATE TABLE event_artifacts (
  event_id BLOB NOT NULL REFERENCES events(id),
  ordinal INTEGER NOT NULL,
  artifact_id BLOB NOT NULL CHECK(length(artifact_id)=32),
  role TEXT NOT NULL,
  PRIMARY KEY(event_id, ordinal)
) WITHOUT ROWID;

CREATE INDEX events_type_seq ON events(type, ingest_seq);
CREATE INDEX events_trace ON events(trace_id, ingest_seq);
CREATE INDEX events_graph_revision ON events(graph_revision) WHERE graph_revision IS NOT NULL;

CREATE TABLE ingest_state (
  singleton INTEGER PRIMARY KEY CHECK(singleton=1),
  last_acked_ingest_seq INTEGER NOT NULL DEFAULT 0,
  last_acked_event_id BLOB NULL CHECK(last_acked_event_id IS NULL OR length(last_acked_event_id)=16)
);
INSERT INTO ingest_state(singleton,last_acked_ingest_seq,last_acked_event_id) VALUES(1,0,NULL);

PRAGMA user_version=1;

@0xa93ec2d4ad73b6c1;

using C = import "common.capnp";
using E = import "events.capnp";

struct Property {
  namespace @0 :Text;
  key @1 :Text;
  value @2 :C.Value;
  authority @3 :Text;
  provenance @4 :C.MaybeUuid;
  validFromRevision @5 :UInt64;
  validToRevision @6 :UInt64; # 0 means current
}

struct Node {
  id @0 :C.Uuid;
  kinds @1 :List(Text);
  properties @2 :List(Property);
  createdRevision @3 :UInt64;
  deletedRevision @4 :UInt64; # 0 means current
}

struct Edge {
  id @0 :C.Uuid;
  source @1 :C.Uuid;
  relation @2 :Text;
  target @3 :C.Uuid;
  dimension @4 :Text;
  properties @5 :List(Property);
  authority @6 :Text;
  provenance @7 :C.MaybeUuid;
  validFromRevision @8 :UInt64;
  validToRevision @9 :UInt64;
}

enum PropertyOp {
  equals @0;
  notEquals @1;
  exists @2;
  notExists @3;
}

struct PropertyFilter {
  namespace @0 :Text;
  key @1 :Text;
  op @2 :PropertyOp;
  value @3 :C.Value; # ignored for exists/notExists
}

struct NodeSelector {
  ids @0 :List(C.Uuid);
  kinds @1 :List(Text);
  propertyFilters @2 :List(PropertyFilter);
}

enum Direction { outgoing @0; incoming @1; both @2; }

struct Traversal {
  relations @0 :List(Text);
  dimensions @1 :List(Text);
  direction @2 :Direction;
  maxDepth @3 :UInt16;
}

struct GraphQuery {
  atRevision @0 :UInt64; # 0 means current
  roots @1 :NodeSelector;
  traversal @2 :Traversal;
  limit @3 :UInt32; # 0 means configured default
}

struct QueryResult {
  revision @0 :UInt64;
  nodes @1 :List(Node);
  edges @2 :List(Edge);
}

struct PathQuery {
  atRevision @0 :UInt64;
  source @1 :C.Uuid;
  target @2 :C.Uuid;
  relations @3 :List(Text);
  dimensions @4 :List(Text);
  direction @5 :Direction;
  maxDepth @6 :UInt16;
  maxPaths @7 :UInt32;
}

struct Path {
  nodes @0 :List(C.Uuid);
  edges @1 :List(C.Uuid);
}

struct PathResult {
  revision @0 :UInt64;
  paths @1 :List(Path);
}

struct Alias {
  namespace @0 :Text;
  alias @1 :Text;
  node @2 :C.Uuid;
  authority @3 :Text;
}

struct Mutation {
  union {
    createNode @0 :CreateNode;
    deleteNode @1 :C.Uuid;
    addKind @2 :NodeKind;
    endKind @3 :NodeKind;
    setProperty @4 :NodeProperty;
    endProperty @5 :PropertyKey;
    createEdge @6 :CreateEdge;
    endEdge @7 :C.Uuid;
    setEdgeProperty @8 :EdgeProperty;
    endEdgeProperty @9 :EdgePropertyKey;
    putProvenance @10 :C.Provenance;
    addAlias @11 :Alias;
    endAlias @12 :Alias;
  }

  struct CreateNode { id @0 :C.Uuid; kinds @1 :List(Text); }
  struct NodeKind { node @0 :C.Uuid; kind @1 :Text; }
  struct NodeProperty { node @0 :C.Uuid; property @1 :Property; }
  struct PropertyKey { node @0 :C.Uuid; namespace @1 :Text; key @2 :Text; }
  struct CreateEdge {
    id @0 :C.Uuid;
    source @1 :C.Uuid;
    relation @2 :Text;
    target @3 :C.Uuid;
    dimension @4 :Text;
    authority @5 :Text;
    provenance @6 :C.MaybeUuid;
  }
  struct EdgeProperty { edge @0 :C.Uuid; property @1 :Property; }
  struct EdgePropertyKey { edge @0 :C.Uuid; namespace @1 :Text; key @2 :Text; }
}

struct PropertyCondition {
  node @0 :C.Uuid;
  namespace @1 :Text;
  key @2 :Text;
  value @3 :C.Value;
}

struct RelationCondition {
  source @0 :C.Uuid;
  relation @1 :Text;
  target @2 :C.Uuid;
}

struct CardinalityCondition {
  node @0 :C.Uuid;
  relation @1 :Text;
  direction @2 :Direction;
  min @3 :UInt32;
  max @4 :UInt32; # UInt32 max means unbounded
}

struct Precondition {
  union {
    revisionEquals @0 :UInt64;
    nodeExists @1 :C.Uuid;
    nodeAbsent @2 :C.Uuid;
    edgeExists @3 :C.Uuid;
    edgeAbsent @4 :C.Uuid;
    propertyEquals @5 :PropertyCondition;
    propertyAbsent @6 :Mutation.PropertyKey;
    relationExists @7 :RelationCondition;
    relationAbsent @8 :RelationCondition;
    cardinality @9 :CardinalityCondition;
  }
}

struct EventEntity {
  id @0 :C.Uuid;
  role @1 :Text;
}

struct EventArtifact {
  artifact @0 :C.ArtifactRef;
  role @1 :Text;
}

struct EventEnvelope {
  id @0 :C.Uuid;
  type @1 :Text;
  schemaMajor @2 :UInt16;
  schemaMinor @3 :UInt16;
  source @4 :C.Uuid;
  trace @5 :C.TraceContext;
  graphRevision @6 :UInt64; # producer supplies 0; graphd fills committed revision for tx events
  entities @7 :List(EventEntity);
  artifacts @8 :List(EventArtifact);
  payload @9 :E.Payload;
  observedWallNs @10 :Int64;
  observedMonotonicNs @11 :UInt64;
}

struct GraphTransaction {
  id @0 :C.Uuid;
  trace @1 :C.TraceContext;
  authority @2 :Text;
  expectedRevision @3 :UInt64;
  preconditions @4 :List(Precondition);
  mutations @5 :List(Mutation);
  events @6 :List(EventEnvelope);
}

struct CommitResult {
  transactionId @0 :C.Uuid;
  previousRevision @1 :UInt64;
  newRevision @2 :UInt64;
  changedIds @3 :List(C.Uuid);
  graphCommittedEvent @4 :C.Uuid;
}

struct GraphDelta {
  previousRevision @0 :UInt64;
  revision @1 :UInt64;
  changedIds @2 :List(C.Uuid);
}

struct AliasResult {
  namespace @0 :Text;
  alias @1 :Text;
  nodes @2 :List(C.Uuid);
}

interface GraphSubscription {
  next @0 () -> (status :C.RpcStatus, delta :GraphDelta);
  cancel @1 () -> (status :C.RpcStatus);
}

struct EventRecord {
  ingestSeq @0 :UInt64;
  event @1 :EventEnvelope;
}

interface EventSubscription {
  next @0 () -> (status :C.RpcStatus, record :EventRecord);
  cancel @1 () -> (status :C.RpcStatus);
}

interface ArtifactUpload {
  write @0 (chunk :Data) -> (status :C.RpcStatus); # chunk <= 1 MiB
  finish @1 () -> (status :C.RpcStatus, artifact :C.ArtifactRef);
  abort @2 () -> (status :C.RpcStatus);
}

interface ArtifactDownload {
  next @0 () -> (status :C.RpcStatus, chunk :Data, done :Bool); # chunk <= 1 MiB
  cancel @1 () -> (status :C.RpcStatus);
}

interface GraphService {
  handshake @0 (request :C.HandshakeRequest) -> (status :C.RpcStatus, response :C.HandshakeResponse);
  revision @1 () -> (status :C.RpcStatus, revision :UInt64);
  getNode @2 (id :C.Uuid, atRevision :UInt64) -> (status :C.RpcStatus, node :Node);
  query @3 (query :GraphQuery) -> (status :C.RpcStatus, result :QueryResult);
  commit @4 (transaction :GraphTransaction) -> (status :C.RpcStatus, result :CommitResult);
  subscribe @5 (query :GraphQuery, afterRevision :UInt64) -> (status :C.RpcStatus, subscription :GraphSubscription);
  readEvents @6 (afterIngestSeq :UInt64, limit :UInt32) -> (status :C.RpcStatus, events :List(EventRecord));
  subscribeEvents @7 (afterIngestSeq :UInt64) -> (status :C.RpcStatus, subscription :EventSubscription);
  getEvent @8 (id :C.Uuid) -> (status :C.RpcStatus, record :EventRecord);
  enqueueEvent @9 (event :EventEnvelope) -> (status :C.RpcStatus, ingestSeq :UInt64);
  beginArtifactUpload @10 (
    mediaType :Text,
    protection :C.ProtectionClass,
    expectedLength :UInt64,
    expectedId :C.MaybeArtifactId
  ) -> (status :C.RpcStatus, upload :ArtifactUpload);
  openArtifact @11 (id :C.ArtifactId) -> (status :C.RpcStatus, artifact :C.ArtifactRef, download :ArtifactDownload);
  resolveAlias @12 (namespace :Text, alias :Text, atRevision :UInt64) -> (status :C.RpcStatus, result :AliasResult);
  paths @13 (query :PathQuery) -> (status :C.RpcStatus, result :PathResult);
  getProvenance @14 (id :C.Uuid) -> (status :C.RpcStatus, provenance :C.Provenance);
}

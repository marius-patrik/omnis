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

struct NodeSelector {
  ids @0 :List(C.Uuid);
  kinds @1 :List(Text);
  namespaces @2 :List(Text);
  text @3 :Text;
}

struct Traversal {
  relations @0 :List(Text);
  direction @1 :Direction;
  maxDepth @2 :UInt16;
  enum Direction { outgoing @0; incoming @1; both @2; }
}

struct GraphQuery {
  atRevision @0 :UInt64; # 0 means current
  roots @1 :NodeSelector;
  traversal @2 :Traversal;
  limit @3 :UInt32;
}

struct QueryResult {
  revision @0 :UInt64;
  nodes @1 :List(Node);
  edges @2 :List(Edge);
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
  }

  struct CreateNode { id @0 :C.Uuid; kinds @1 :List(Text); }
  struct NodeKind { node @0 :C.Uuid; kind @1 :Text; }
  struct NodeProperty { node @0 :C.Uuid; property @1 :Property; }
  struct PropertyKey { node @0 :C.Uuid; namespace @1 :Text; key @2 :Text; }
  struct CreateEdge {
    id @0 :C.Uuid; source @1 :C.Uuid; relation @2 :Text; target @3 :C.Uuid;
    dimension @4 :Text; authority @5 :Text; provenance @6 :C.MaybeUuid;
  }
  struct EdgeProperty { edge @0 :C.Uuid; property @1 :Property; }
  struct EdgePropertyKey { edge @0 :C.Uuid; namespace @1 :Text; key @2 :Text; }
}

struct Precondition {
  union {
    revisionEquals @0 :UInt64;
    nodeExists @1 :C.Uuid;
    nodeAbsent @2 :C.Uuid;
    edgeExists @3 :C.Uuid;
  }
}

struct EventEnvelope {
  id @0 :C.Uuid;
  type @1 :Text;
  schemaMajor @2 :UInt16;
  schemaMinor @3 :UInt16;
  source @4 :C.Uuid;
  trace @5 :C.TraceContext;
  graphRevision @6 :UInt64; # 0 when event is not tied to a graph revision
  entities @7 :List(C.Uuid);
  artifacts @8 :List(C.ArtifactRef);
  payload @9 :E.Payload;
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
}

struct GraphDelta {
  previousRevision @0 :UInt64;
  revision @1 :UInt64;
  changedIds @2 :List(C.Uuid);
}

interface GraphSubscription {
  next @0 () -> (status :C.RpcStatus, delta :GraphDelta);
  cancel @1 () -> (status :C.RpcStatus);
}

interface OutboxSubscription {
  next @0 () -> (status :C.RpcStatus, event :EventEnvelope, ingestSeq :UInt64);
  ack @1 (eventId :C.Uuid, ingestSeq :UInt64) -> (status :C.RpcStatus);
  cancel @2 () -> (status :C.RpcStatus);
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
  outbox @6 (afterIngestSeq :UInt64) -> (status :C.RpcStatus, subscription :OutboxSubscription);
  enqueueEvent @7 (event :EventEnvelope) -> (status :C.RpcStatus, ingestSeq :UInt64);
  beginArtifactUpload @8 (
    mediaType :Text,
    protection :C.ProtectionClass,
    expectedLength :UInt64,
    expectedId :C.MaybeArtifactId
  ) -> (status :C.RpcStatus, upload :ArtifactUpload);
  openArtifact @9 (id :C.ArtifactId) -> (status :C.RpcStatus, artifact :C.ArtifactRef, download :ArtifactDownload);
}

# EXT_structural_metadata with BMesh

## Contributors

- K. S. Ernest (iFire) Lee, Individual Contributor / https://github.com/fire
- Based on principles from FB_ngon_encoding by Pär Winzell and Michael Bunnell (Facebook)

## Status

Active Development

## Dependencies

Written against the glTF 2.0 spec, superseding FB_ngon_encoding.
Compatible with EXT_mesh_manifold for manifold topology validation.

## References

The BMesh data structure is described in:

- Gueorguieva, Stefka and Marcheix, Davi. 1994. "Non-manifold boundary representation for solid modeling."
- BMeshUnity implementation: https://github.com/eliemichel/BMeshUnity.git

## Overview

While glTF can only deliver a polygon mesh after it's been decomposed into triangles, there are cases where access to the full BMesh topology is still useful. BMesh provides a non-manifold boundary representation with vertices, edges, loops, and faces that enables complex geometric operations.

This implementation provides **property table-based BMesh encoding** that stores complete topology information in EXT_structural_metadata property tables for performance while maintaining full glTF 2.0 compatibility.

The `EXT_structural_metadata` glTF extension solves the problem of topological data loss when models with quads and n-gons are converted to glTF's triangle-only format. It works by embedding the **BMesh** data structure, allowing for reconstruction of the original model.

What makes BMesh so powerful is its ability to represent complex, **non-manifold** geometry. Unlike mesh formats that limit an edge to connecting only two faces, BMesh uses a system of **radial loops** (`radial_next` and `radial_prev` pointers). This is like a book spine that can connect every single page, not just the two covers.

`EXT_structural_metadata` allows for the preservation of models where multiple faces meet at a single edge, ensuring the artist's intent is maintained.

## Key Features

### Property Table Storage

- **High Performance**: All BMesh data stored in binary property tables for optimal memory usage
- **glTF 2.0 Compliance**: Follows standard EXT_structural_metadata property table patterns
- **Scalable**: Efficient for meshes of any size
- **Standard Attributes**: Uses glTF 2.0 attribute naming conventions (TEXCOORD_0, etc.)
- **Non-manifold Support**: Complete support for non-manifold edges and vertices

## Extension Structure

glTF property table format (all data stored in property tables):

```json
{
  "extensions": {
    "EXT_structural_metadata": {
      "schema": {
        "id": "BMesh_schema",
        "classes": {
          "vertex": {...},
          "edge": {...},
          "loop": {...},
          "face": {...}
        }
      },
      "propertyTables": [
        {
          "name": "BMesh Vertices",
          "class": "vertex",
          "count": 10000,
          "properties": {
            "position": {"values": 0},
            "connectedEdges": {"values": 1}
          }
        },
        {
          "name": "BMesh Edges",
          "class": "edge",
          "count": 15000,
          "properties": {
            "vertex0": {"values": 2},
            "vertex1": {"values": 3},
            "adjacentFaces": {"values": 4},
            "manifoldStatus": {"values": 5}
          }
        },
        {
          "name": "BMesh Loops",
          "class": "loop",
          "count": 20000,
          "properties": {
            "vertex": {"values": 6},
            "edge": {"values": 7},
            "face": {"values": 8},
            "next": {"values": 9},
            "prev": {"values": 10},
            "radialNext": {"values": 11},
            "radialPrev": {"values": 12}
          }
        },
        {
          "name": "BMesh Faces",
          "class": "face",
          "count": 5000,
          "properties": {
            "vertices": {"values": 13},
            "edges": {"values": 14},
            "loops": {"values": 15},
            "offsets": {"values": 16},
            "normals": {"values": 17}
          }
        }
      ]
    }
  }
}
```

## Implicit Triangle Fan Algorithm

Building on FB_ngon_encoding principles with BMesh enhancements:

### Core Principle

Like FB_ngon_encoding, the **order of triangles and per-triangle vertex indices** holds all information needed to reconstruct BMesh topology. The algorithm uses an enhanced triangulation process:

- For each BMesh face `f`, choose one identifying vertex `v(f)`
- Break the face into a triangle fan, all anchored at `v(f)`
- **Ensure `v(f) != v(f')` for consecutive faces** (mandatory requirement for unambiguous reconstruction)

### Encoding Process (Implicit Layer)

1. **BMesh Face Analysis**: Analyze BMesh faces for triangulation
2. **Enhanced Anchor Selection**: Choose anchor vertex to minimize reconstruction ambiguity
3. **Triangle Fan Generation**: Create triangle fans with vertex ordering
4. **Standard glTF Output**: Produce standard glTF triangles following triangle fan pattern

### Reconstruction Process

1. **Triangle Grouping**: Group consecutive triangles sharing the same `triangle.vertices[0]`
2. **BMesh Face Rebuilding**: Reconstruct BMesh faces from triangle fans
3. **Topology Inference**: Infer BMesh edge and loop structure from face connectivity
4. **Validation**: Validate reconstructed BMesh for topological consistency

## Property Table Layouts

All BMesh topology data is stored in EXT_structural_metadata property tables using efficient binary layouts:

### Vertex Properties

- **position**: `Vec3<f32>` (12 bytes per vertex) - 3D coordinates
- **connectedEdges**: Variable-length edge index arrays with offset indexing
- **attributes**: Standard glTF attributes (POSITION, NORMAL, TEXCOORD_0, etc.)

### Edge Properties

- **vertex0**: `u32` - First vertex index
- **vertex1**: `u32` - Second vertex index
- **adjacentFaces**: Variable-length face index arrays with offset indexing
- **manifoldStatus**: `u8` - Manifold status flag
  - `0`: Confirmed non-manifold
  - `1`: Confirmed manifold
  - `255`: Unknown status
- **attributes**: Custom edge data with `_` prefix naming

### Loop Properties

- **vertex**: `u32` - Corner vertex index
- **edge**: `u32` - Outgoing edge index
- **face**: `u32` - Containing face index
- **next**: `u32` - Next loop in face
- **prev**: `u32` - Previous loop in face
- **radialNext**: `u32` - Next loop around edge
- **radialPrev**: `u32` - Previous loop around edge
- **attributes**: glTF 2.0 compliant attributes (TEXCOORD_0, COLOR_0, etc.)

### Face Properties

- **vertices**: Variable-length vertex index arrays
- **edges**: Variable-length edge index arrays
- **loops**: Variable-length loop index arrays
- **offsets**: `[u32; 3]` - Start offsets for vertices, edges, loops arrays
- **normals**: `Vec3<f32>` - Face normal vectors
- **attributes**: Custom face data with `_` prefix naming

### Variable-Length Array Encoding

For arrays with variable length (face vertices, edges, loops), data is stored as:

1. **Packed Data Arrays**: Concatenated array elements in property table values
2. **Offset Arrays**: Start indices for each element's data in separate property
3. **Access Pattern**: `data[offsets[i]:offsets[i+1]]` gives element i's array

## Implementation Requirements

All EXT_structural_metadata BMesh implementations must support:

1. **Property Table Storage**: All topology data in EXT_structural_metadata property tables for performance
2. **glTF 2.0 Compliance**: Standard property table patterns and attribute naming
3. **Triangle Fan Compatibility**: Maintains FB_ngon_encoding reconstruction principles
4. **Complete Topology**: Full BMesh reconstruction with vertices, edges, loops, faces
5. **Graceful Degradation**: Automatic fallback to triangle fan reconstruction when extension unsupported

### Implementation Guidance

**Simple Writers** (minimal implementation):

- Use `manifoldStatus: 255` for all edges (no manifold checking required)
- Store basic BMesh topology without complex validation
- Focus on core property table encoding functionality

**Advanced Writers** (full implementation):

- Perform manifold checking and set appropriate manifold values (0, 1, 255)
- Validate topology during encoding
- Optimize property table layouts for specific use cases

**Readers** (all implementations):

- Handle all three manifold states gracefully
- Provide fallback behavior for unknown manifold status
- Support reconstruction from either implicit triangles or explicit property tables

## Advantages over FB_ngon_encoding

1. **Complete Topology**: Full BMesh structure with edges and loops, not just faces
2. **Performance Optimized**: Binary property table storage instead of JSON arrays
3. **Non-manifold Support**: Explicit handling of non-manifold geometry
4. **Attribute Rich**: Comprehensive attribute support at all topology levels
5. **glTF 2.0 Native**: Follows EXT_structural_metadata patterns and naming conventions
6. **Backward Compatible**: Falls back gracefully to triangle fan reconstruction

## Algorithm Details

### Enhanced Triangle Fan Encoding

```javascript
// Implicit encoding - maintains triangle fan pattern for compatibility
function encodeBmeshImplicit(bmeshFaces) {
  const triangles = [];
  let prevAnchor = -1;

  for (const face of bmeshFaces) {
    const vertices = face.vertices;
    // MANDATORY: Select anchor different from previous face
    const candidates = vertices.filter((v) => v !== prevAnchor);
    const anchor =
      candidates.length > 0 ? Math.min(...candidates) : vertices[0];

    // This MUST be different from prevAnchor for correct reconstruction
    if (anchor === prevAnchor && vertices.length > 1) {
      throw new Error(
        "Cannot ensure v(f) != v(f') - algorithm requirement violated"
      );
    }

    prevAnchor = anchor;

    const n = vertices.length;
    const anchorIdx = vertices.indexOf(anchor);

    // Create triangle fan from anchor
    for (let i = 2; i < n; i++) {
      const v1Idx = (anchorIdx + i - 1) % n;
      const v2Idx = (anchorIdx + i) % n;
      const triangle = [anchor, vertices[v1Idx], vertices[v2Idx]];
      triangles.push(triangle);
    }
  }

  return triangles;
}

// Property table-based BMesh reconstruction
function decodeBmeshFromPropertyTables(gltfData) {
  const bmesh = {
    vertices: new Map(),
    edges: new Map(),
    loops: new Map(),
    faces: new Map(),
  };

  const ext = gltfData.extensions.EXT_structural_metadata;
  const propertyTables = ext.propertyTables;

  // Find BMesh property tables
  const vertexTable = propertyTables.find(t => t.class === 'vertex');
  const edgeTable = propertyTables.find(t => t.class === 'edge');
  const loopTable = propertyTables.find(t => t.class === 'loop');
  const faceTable = propertyTables.find(t => t.class === 'face');

  // Reconstruct vertices from property table
  if (vertexTable) {
    const positions = readPropertyTableValues(gltfData, vertexTable.properties.position);
    for (let i = 0; i < vertexTable.count; i++) {
      bmesh.vertices.set(i, {
        id: i,
        position: [
          positions[i * 3],
          positions[i * 3 + 1],
          positions[i * 3 + 2],
        ],
        edges: [],
        attributes: {},
      });
    }
  }

  // Reconstruct edges from property table
  if (edgeTable) {
    const vertex0s = readPropertyTableValues(gltfData, edgeTable.properties.vertex0);
    const vertex1s = readPropertyTableValues(gltfData, edgeTable.properties.vertex1);
    const manifoldFlags = readPropertyTableValues(gltfData, edgeTable.properties.manifoldStatus);

    for (let i = 0; i < edgeTable.count; i++) {
      const edge = {
        id: i,
        vertices: [vertex0s[i], vertex1s[i]],
        faces: [],
        manifold:
          manifoldFlags[i] === 1 ? true : manifoldFlags[i] === 0 ? false : null,
        attributes: {},
      };
      bmesh.edges.set(i, edge);
    }
  }

  // Reconstruct loops from property table
  if (loopTable) {
    const vertices = readPropertyTableValues(gltfData, loopTable.properties.vertex);
    const edges = readPropertyTableValues(gltfData, loopTable.properties.edge);
    const faces = readPropertyTableValues(gltfData, loopTable.properties.face);
    const nexts = readPropertyTableValues(gltfData, loopTable.properties.next);
    const prevs = readPropertyTableValues(gltfData, loopTable.properties.prev);
    const radialNexts = readPropertyTableValues(gltfData, loopTable.properties.radialNext);
    const radialPrevs = readPropertyTableValues(gltfData, loopTable.properties.radialPrev);

    for (let i = 0; i < loopTable.count; i++) {
      bmesh.loops.set(i, {
        id: i,
        vertex: vertices[i],
        edge: edges[i],
        face: faces[i],
        next: nexts[i],
        prev: prevs[i],
        radial_next: radialNexts[i],
        radial_prev: radialPrevs[i],
        attributes: {},
      });
    }
  }

  // Reconstruct faces from property table
  if (faceTable) {
    const faceVertices = readPropertyTableValues(gltfData, faceTable.properties.vertices);
    const faceOffsets = readPropertyTableValues(gltfData, faceTable.properties.offsets);
    const faceNormals = readPropertyTableValues(gltfData, faceTable.properties.normals);

    for (let i = 0; i < faceTable.count; i++) {
      const vertexStart = faceOffsets[i * 3];
      const vertexEnd = faceOffsets[i * 3 + 1];

      const face = {
        id: i,
        vertices: faceVertices.slice(vertexStart, vertexEnd),
        edges: [],
        loops: [],
        normal: [
          faceNormals[i * 3],
          faceNormals[i * 3 + 1],
          faceNormals[i * 3 + 2],
        ],
        attributes: {},
      };
      bmesh.faces.set(i, face);
    }
  }

  return bmesh;
}

function readPropertyTableValues(gltfData, propertyRef) {
  // Implementation would read from glTF buffers based on property reference
  // This is a simplified placeholder
  return [];
}
```

## glTF Schema

- **JSON schema**: `glTF.EXT_structural_metadata.bmesh.schema.json`
- **Example schema**: `bmesh_schema_example.json`

## Known Implementations

- Aria BMesh Domain (Elixir) - In Development
- VRM Add-on for Blender (Python) - Active Development

## BMesh Data Structures

The following BMesh structures are preserved through property table encoding:

### Vertex

- **Position**: 3D coordinates (x, y, z) stored in `position` property
- **Connected Edges**: Edge adjacency data in variable-length `connectedEdges` property
- **Attributes**: Standard glTF attributes (POSITION, NORMAL, TEXCOORD_0, etc.)

### Edge

- **Vertices**: Two vertex references stored as `vertex0`, `vertex1` properties
- **Adjacent Faces**: Variable-length face index arrays in `adjacentFaces` property
- **Manifold Status**: Single byte flag in `manifoldStatus` property compatible with EXT_mesh_manifold
  - `0`: Confirmed non-manifold
  - `1`: Confirmed manifold (oriented 2-manifold)
  - `255`: Unknown status (no manifold checking performed)
- **Attributes**: Custom edge data with `_` prefix naming

### Loop

- **Vertex**: Corner vertex reference in `vertex` property
- **Edge**: Outgoing edge from vertex in `edge` property
- **Face**: Containing face reference in `face` property
- **Navigation**: Next/previous loop in face in `next`/`prev` properties, radial next/previous around edge in `radialNext`/`radialPrev` properties
- **Topology**: All navigation stored as separate properties per loop
- **Attributes**: Per-corner data using glTF naming (TEXCOORD_0, COLOR_0, etc.)

### Face

- **Vertices**: Variable-length vertex index arrays in `vertices` property
- **Edges**: Variable-length edge index arrays in `edges` property
- **Loops**: Variable-length loop index arrays in `loops` property
- **Normal**: Face normal vector in `normal` property
- **Attributes**: Custom face data with `_` prefix naming

### Topological Relationships

- **Vertex-Edge**: One-to-many (vertex connects to multiple edges)
- **Edge-Face**: One-to-many (edge shared by multiple faces, enables non-manifold)
- **Face-Loop**: One-to-many (face has loops for each corner)
- **Loop Navigation**: Circular lists around faces and radially around edges

## No Per-Face Materials

Per-face materials were considered and intentionally excluded from EXT_structural_metadata BMesh implementation.

EXT_structural_metadata focuses purely on **topology preservation** rather than solving the material assignment problem, which is better handled at the glTF primitive and node levels.

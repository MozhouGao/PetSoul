"""
Bind the frozen dog skeleton to a static GLB and embed animation clips.

This is the rig used when Blender is not installed. Weights are inverse-distance
to bone segments (four influences). Rest rotations are identity, so clip
rotations are local offsets on that bind pose.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from dog_skeleton import BONE_NAMES, PARENT_OF, height_scale, place_on_mesh

GLB_MAGIC = 0x46546C67
JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942
FLOAT = 5126
USHORT = 5123


def read_glb(path: Path) -> Tuple[dict, bytes]:
    data = Path(path).read_bytes()
    if len(data) < 20:
        raise ValueError("file is not a GLB")
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != GLB_MAGIC or version != 2:
        raise ValueError("file is not a GLB 2.0")
    offset = 12
    gltf = None
    blob = b""
    while offset + 8 <= len(data):
        chunk_len, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset:offset + chunk_len]
        offset += chunk_len
        if chunk_type == JSON_CHUNK:
            gltf = json.loads(chunk.decode("utf-8").rstrip(" \t\r\n\x00"))
        elif chunk_type == BIN_CHUNK:
            blob = chunk
    if gltf is None:
        raise ValueError("GLB has no JSON chunk")
    return gltf, blob


def write_glb(path: Path, gltf: dict, blob: bytes) -> None:
    raw = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    raw += b" " * ((4 - len(raw) % 4) % 4)
    bin_chunk = bytes(blob)
    bin_chunk += b"\x00" * ((4 - len(bin_chunk) % 4) % 4)
    total = 12 + 8 + len(raw) + 8 + len(bin_chunk)
    out = bytearray()
    out += struct.pack("<III", GLB_MAGIC, 2, total)
    out += struct.pack("<II", len(raw), JSON_CHUNK)
    out += raw
    out += struct.pack("<II", len(bin_chunk), BIN_CHUNK)
    out += bin_chunk
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(out)


def _accessor_array(gltf: dict, blob: bytes, index: int) -> np.ndarray:
    acc = gltf["accessors"][index]
    if acc.get("componentType") != FLOAT or acc.get("type") != "VEC3":
        raise ValueError("only float VEC3 positions can be rigged")
    view = gltf["bufferViews"][acc["bufferView"]]
    start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = view.get("byteStride", 12)
    count = acc["count"]
    points = np.empty((count, 3), dtype=np.float32)
    for i in range(count):
        points[i] = struct.unpack_from("<fff", blob, start + i * stride)
    return points


def _largest_mesh(gltf: dict, blob: bytes) -> Tuple[int, int, np.ndarray]:
    best = None
    for node_index, node in enumerate(gltf.get("nodes", [])):
        if "mesh" not in node:
            continue
        mesh_index = node["mesh"]
        mesh = gltf["meshes"][mesh_index]
        for prim_index, prim in enumerate(mesh.get("primitives", [])):
            attrs = prim.get("attributes", {})
            if "POSITION" not in attrs:
                continue
            if gltf["accessors"][attrs["POSITION"]].get("componentType") != FLOAT:
                continue
            points = _accessor_array(gltf, blob, attrs["POSITION"])
            if best is None or len(points) > len(best[2]):
                best = (node_index, mesh_index, points)
    if best is None:
        raise ValueError("GLB has no float mesh to rig")
    return best


def _segment_distance(points: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ab = b - a
    denom = float(np.dot(ab, ab))
    if denom < 1e-12:
        return np.linalg.norm(points - a, axis=1)
    t = np.clip(((points - a) @ ab) / denom, 0.0, 1.0)
    closest = a + t[:, None] * ab
    return np.linalg.norm(points - closest, axis=1)


def _skin_weights(vertices: np.ndarray, world: Dict[str, np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
    segments = []
    for name, parent in PARENT_OF.items():
        if parent is None:
            continue
        segments.append((BONE_NAMES.index(name), world[parent], world[name]))
    dists = np.stack([
        _segment_distance(vertices, a, b) for _, a, b in segments
    ], axis=1)
    bone_ids = np.array([idx for idx, _, _ in segments], dtype=np.uint16)
    weights = np.zeros((len(vertices), 4), dtype=np.float32)
    joints = np.zeros((len(vertices), 4), dtype=np.uint16)
    for v in range(len(vertices)):
        order = np.argsort(dists[v])[:4]
        d = dists[v, order]
        w = 1.0 / (d * d + 1e-4)
        w = w / w.sum()
        weights[v] = w.astype(np.float32)
        joints[v] = bone_ids[order]
    return joints, weights


def _world_from_local(local: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    world = {}
    for name in BONE_NAMES:
        parent = PARENT_OF[name]
        world[name] = local[name].copy() if parent is None else world[parent] + local[name]
    return world


def _inv_bind(world: np.ndarray) -> np.ndarray:
    mat = np.eye(4, dtype=np.float32)
    mat[:3, 3] = world.astype(np.float32)
    return np.linalg.inv(mat).T.reshape(-1).astype(np.float32)


def _append(blob: bytearray, payload: bytes) -> int:
    while len(blob) % 4:
        blob.append(0)
    offset = len(blob)
    blob.extend(payload)
    return offset


def _add_view(gltf: dict, offset: int, length: int) -> int:
    gltf["bufferViews"].append({"buffer": 0, "byteOffset": offset, "byteLength": length})
    return len(gltf["bufferViews"]) - 1


def _add_accessor(gltf: dict, view: int, count: int, ctype: int, atype: str, offset: int = 0) -> int:
    gltf["accessors"].append({
        "bufferView": view,
        "byteOffset": offset,
        "componentType": ctype,
        "count": count,
        "type": atype,
    })
    return len(gltf["accessors"]) - 1


def _scale_translation_offsets(clip: dict, scale: float) -> dict:
    translations = {}
    for bone, offsets in clip.get("translations", {}).items():
        translations[bone] = np.asarray(offsets, dtype=np.float64) * np.array([scale, scale, scale])
    return {
        "times": np.asarray(clip["times"], dtype=np.float64),
        "rotations": clip["rotations"],
        "translations": translations,
    }


def rig_glb(src: Path, dst: Path, clips: Dict[str, dict]) -> List[str]:
    """Write a skinned GLB with one animation per clip. Returns clip names in order."""
    gltf, blob_in = read_glb(src)
    node_index, mesh_index, vertices = _largest_mesh(gltf, blob_in)
    local = place_on_mesh(vertices)
    world = _world_from_local(local)
    scale = height_scale(vertices)
    joints_attr, weights_attr = _skin_weights(np.asarray(vertices, dtype=np.float64), world)

    blob = bytearray(blob_in)
    gltf.setdefault("bufferViews", [])
    gltf.setdefault("accessors", [])
    gltf.setdefault("nodes", [])
    gltf.setdefault("buffers", [{"byteLength": len(blob_in)}])

    j_off = _append(blob, joints_attr.astype("<u2").tobytes())
    j_view = _add_view(gltf, j_off, joints_attr.size * 2)
    j_acc = _add_accessor(gltf, j_view, len(joints_attr), USHORT, "VEC4")

    w_off = _append(blob, weights_attr.astype("<f4").tobytes())
    w_view = _add_view(gltf, w_off, weights_attr.size * 4)
    w_acc = _add_accessor(gltf, w_view, len(weights_attr), FLOAT, "VEC4")

    for prim in gltf["meshes"][mesh_index]["primitives"]:
        if "POSITION" in prim.get("attributes", {}):
            prim["attributes"]["JOINTS_0"] = j_acc
            prim["attributes"]["WEIGHTS_0"] = w_acc

    children: Dict[str, List[int]] = {name: [] for name in BONE_NAMES}
    bone_nodes: Dict[str, int] = {}
    for name in BONE_NAMES:
        node = {
            "name": name,
            "translation": [float(v) for v in local[name]],
            "rotation": [0.0, 0.0, 0.0, 1.0],
        }
        bone_nodes[name] = len(gltf["nodes"])
        gltf["nodes"].append(node)
    for name in BONE_NAMES:
        parent = PARENT_OF[name]
        if parent is not None:
            children[parent].append(bone_nodes[name])
    for name, kids in children.items():
        if kids:
            gltf["nodes"][bone_nodes[name]]["children"] = kids

    ibms = np.stack([_inv_bind(world[name]) for name in BONE_NAMES], axis=0)
    ibm_off = _append(blob, ibms.astype("<f4").tobytes())
    ibm_view = _add_view(gltf, ibm_off, ibms.size * 4)
    ibm_acc = _add_accessor(gltf, ibm_view, len(BONE_NAMES), FLOAT, "MAT4")

    skin_index = len(gltf.setdefault("skins", []))
    gltf["skins"].append({
        "name": "dog_v1",
        "inverseBindMatrices": ibm_acc,
        "joints": [bone_nodes[name] for name in BONE_NAMES],
        "skeleton": bone_nodes["root"],
    })
    mesh_node = gltf["nodes"][node_index]
    mesh_node["skin"] = skin_index
    mesh_node.setdefault("children", []).append(bone_nodes["root"])

    names = []
    gltf.setdefault("animations", [])
    for clip_name, clip in clips.items():
        scaled = _scale_translation_offsets(clip, scale)
        _add_animation(gltf, blob, bone_nodes, local, clip_name, scaled)
        names.append(clip_name)

    gltf["buffers"][0]["byteLength"] = len(blob)
    write_glb(dst, gltf, bytes(blob))
    return names


def _add_animation(gltf, blob, bone_nodes, rest_local, clip_name, clip) -> None:
    times = np.asarray(clip["times"], dtype=np.float32)
    t_off = _append(blob, times.tobytes())
    t_view = _add_view(gltf, t_off, times.nbytes)
    t_acc = _add_accessor(gltf, t_view, len(times), FLOAT, "SCALAR")
    channels = []
    samplers = []

    def sampler_for(values: np.ndarray, atype: str) -> int:
        raw = np.asarray(values, dtype=np.float32)
        off = _append(blob, raw.tobytes())
        view = _add_view(gltf, off, raw.nbytes)
        acc = _add_accessor(gltf, view, len(times), FLOAT, atype)
        samplers.append({"input": t_acc, "output": acc, "interpolation": "LINEAR"})
        return len(samplers) - 1

    for bone, quats in clip["rotations"].items():
        if bone not in bone_nodes:
            continue
        sid = sampler_for(quats, "VEC4")
        channels.append({"sampler": sid, "target": {"node": bone_nodes[bone], "path": "rotation"}})

    for bone, offsets in clip["translations"].items():
        if bone not in bone_nodes:
            continue
        rest = rest_local[bone]
        full = np.asarray(offsets, dtype=np.float64) + rest
        sid = sampler_for(full, "VEC3")
        channels.append({"sampler": sid, "target": {"node": bone_nodes[bone], "path": "translation"}})

    gltf["animations"].append({"name": clip_name, "samplers": samplers, "channels": channels})


def animation_names(path: Path) -> List[str]:
    gltf, _ = read_glb(path)
    return [anim.get("name", "") for anim in gltf.get("animations", [])]


def make_box_glb(path: Path, size: float = 1.0) -> None:
    """Unrigged triangle cube, used by tests and as a rig smoke fixture."""
    s = size * 0.5
    corners = np.array([
        [-s, 0, -s], [s, 0, -s], [s, 0, s], [-s, 0, s],
        [-s, size, -s], [s, size, -s], [s, size, s], [-s, size, s],
    ], dtype=np.float32)
    faces = [
        (0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6),
        (0, 4, 5), (0, 5, 1), (1, 5, 6), (1, 6, 2),
        (2, 6, 7), (2, 7, 3), (3, 7, 4), (3, 4, 0),
    ]
    indices = np.array(faces, dtype=np.uint16).reshape(-1)
    pos = corners.tobytes()
    idx = indices.tobytes()
    blob = bytearray()
    pos_off = _append(blob, pos)
    idx_off = _append(blob, idx)
    gltf = {
        "asset": {"version": "2.0", "generator": "petsoul"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "mesh", "mesh": 0}],
        "meshes": [{
            "primitives": [{
                "attributes": {"POSITION": 0},
                "indices": 1,
                "mode": 4,
            }]
        }],
        "buffers": [{"byteLength": len(blob)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": pos_off, "byteLength": len(pos)},
            {"buffer": 0, "byteOffset": idx_off, "byteLength": len(idx)},
        ],
        "accessors": [
            {
                "bufferView": 0, "componentType": FLOAT, "count": 8, "type": "VEC3",
                "min": [-s, 0, -s], "max": [s, size, s],
            },
            {"bufferView": 1, "componentType": USHORT, "count": int(indices.size), "type": "SCALAR"},
        ],
    }
    write_glb(path, gltf, bytes(blob))

"""
Blender background script. Called as:

    blender --background --python tools/rig_dog.py -- in.glb out.glb spec.json

Builds the frozen dog armature, automatic weights, and the clip actions, then
exports a skinned GLB. This file runs inside Blender, not the app interpreter.
"""

import json
import sys

import bpy
from mathutils import Quaternion, Vector


def _args():
    argv = sys.argv
    if "--" not in argv:
        raise SystemExit("expected -- in.glb out.glb spec.json")
    src, dst, spec_path = argv[argv.index("--") + 1:]
    return src, dst, spec_path


def _clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _import_mesh(path):
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("no mesh in GLB")
    return max(meshes, key=lambda obj: len(obj.data.vertices))


def _build_armature(spec):
    arm_data = bpy.data.armatures.new("dog_v1")
    arm_obj = bpy.data.objects.new("dog_v1", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    bones = {}
    for entry in spec["bones"]:
        bone = arm_data.edit_bones.new(entry["name"])
        parent_name = entry["parent"]
        local = Vector(entry["local"])
        if parent_name:
            bone.parent = bones[parent_name]
            bone.head = bones[parent_name].head + local
        else:
            bone.head = local
        bone.tail = bone.head + Vector((0.0, 0.05, 0.0))
        bones[entry["name"]] = bone
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _auto_weight(mesh, armature):
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")


def _add_actions(armature, spec):
    if not armature.animation_data:
        armature.animation_data_create()
    for clip_name, clip in spec["clips"].items():
        action = bpy.data.actions.new(clip_name)
        armature.animation_data.action = action
        times = clip["times"]
        for bone_name, keys in clip.get("rotations", {}).items():
            pose_bone = armature.pose.bones.get(bone_name)
            if pose_bone is None:
                continue
            for index, (t, quat) in enumerate(zip(times, keys)):
                pose_bone.rotation_mode = "QUATERNION"
                pose_bone.rotation_quaternion = Quaternion((quat[3], quat[0], quat[1], quat[2]))
                pose_bone.keyframe_insert(data_path="rotation_quaternion", frame=int(round(t * 30)) + 1)
        for bone_name, keys in clip.get("translations", {}).items():
            pose_bone = armature.pose.bones.get(bone_name)
            if pose_bone is None:
                continue
            for t, loc in zip(times, keys):
                pose_bone.location = Vector(loc)
                pose_bone.keyframe_insert(data_path="location", frame=int(round(t * 30)) + 1)
        action.name = clip_name
        track = armature.animation_data.nla_tracks.new()
        track.name = clip_name
        track.strips.new(clip_name, 1, action)


def main():
    src, dst, spec_path = _args()
    spec = json.loads(open(spec_path).read())
    _clear_scene()
    mesh = _import_mesh(src)
    armature = _build_armature(spec)
    _auto_weight(mesh, armature)
    _add_actions(armature, spec)
    bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_animations=True, export_nla_strips=True)


if __name__ == "__main__":
    main()

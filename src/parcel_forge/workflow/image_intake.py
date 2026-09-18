"""Immutable image intake and external OBJ handoff, without model/Isaac imports."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import zlib

from parcel_forge.evidence import make_unique_run_dir, write_json, sha256_file
from parcel_forge.workflow.preflight import ROOT, evaluate

PIN = 'f0124197888c2b733e4eaa65acd81ad9cfda3b79'
TRIPOSR_PIN = '107cefdc244c39106fa830359024f6a2f1c78871'
MAX_FILE = 64 * 1024 * 1024


def png_info(data):
    """Check PNG container/CRC/zlib scanline length; no visual interpretation."""
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('expected PNG input (convert JPEG to PNG first)')
    pos, chunks, compressed, header, ended = 8, [], bytearray(), None, False
    while pos + 12 <= len(data):
        n = struct.unpack('>I', data[pos:pos+4])[0]
        kind = data[pos+4:pos+8]
        if pos + n + 12 > len(data):
            raise ValueError('truncated PNG chunk')
        payload = data[pos+8:pos+8+n]
        crc = struct.unpack('>I', data[pos+8+n:pos+12+n])[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            raise ValueError('PNG CRC mismatch')
        if not chunks and kind != b'IHDR':
            raise ValueError('PNG missing initial IHDR')
        if kind == b'IHDR':
            if header is not None or n != 13:
                raise ValueError('invalid PNG IHDR')
            header = struct.unpack('>IIBBBBB', payload)
        elif kind == b'IDAT':
            compressed.extend(payload)
        elif kind == b'IEND':
            if n:
                raise ValueError('invalid PNG IEND')
            ended = True
        elif kind[:1].isupper() and kind != b'PLTE':
            raise ValueError('unsupported critical PNG chunk')
        chunks.append(kind)
        pos += n + 12
        if ended:
            break
    if not ended or pos != len(data) or not compressed or header is None:
        raise ValueError('incomplete PNG container')
    w, h, depth, color, comp, filt, interlace = header
    if not w or not h or depth != 8 or color not in (2, 6) or comp or filt or interlace:
        raise ValueError('require non-interlaced 8-bit RGB/RGBA PNG')
    row = 1 + w * (3 if color == 2 else 4)
    expected = row * h
    if expected > MAX_FILE:
        raise ValueError('decoded PNG exceeds intake budget')
    dec = zlib.decompressobj()
    raw = dec.decompress(compressed, expected + 1)
    if len(raw) != expected or not dec.eof or dec.unused_data or dec.unconsumed_tail:
        raise ValueError('invalid PNG scanline stream')
    if any(raw[i] > 4 for i in range(0, expected, row)):
        raise ValueError('invalid PNG filter')
    return {'width': w, 'height': h, 'channels': 3 if color == 2 else 4,
            'container_and_scanline_validation': 'pass', 'visual_quality': 'not_tested'}


def obj_info(path):
    """Validate position references and measure 3D extent; not shape fidelity."""
    points, faces = [], []
    for line in path.read_text().splitlines():
        fields = line.split('#', 1)[0].split()
        if not fields:
            continue
        if fields[0] == 'v':
            if len(fields) not in (4, 7):
                raise ValueError('OBJ requires xyz or xyz+rgb vertices')
            xyz = tuple(float(x) for x in fields[1:4])
            if len(fields) == 7 and not all(math.isfinite(float(x)) for x in fields[4:]):
                raise ValueError('non-finite OBJ vertex color')
            if not all(math.isfinite(x) for x in xyz):
                raise ValueError('non-finite OBJ position')
            points.append(xyz)
        elif fields[0] == 'f':
            if len(fields) < 4:
                raise ValueError('OBJ face needs three vertices')
            indices = []
            for token in fields[1:]:
                i = int(token.split('/')[0])
                if i == 0:
                    raise ValueError('OBJ zero index')
                # Negative indices bind to the vertices defined at this line.
                indices.append(i - 1 if i > 0 else len(points) + i)
            faces.append(indices)
    if not points or not faces:
        raise ValueError('OBJ has no surface geometry')
    for face in faces:
        if any(i < 0 or i >= len(points) for i in face) or len(set(face)) < 3:
            raise ValueError('invalid OBJ position reference')
    used = sorted(set(i for face in faces for i in face))
    pts = [points[i] for i in used]
    low = [min(p[a] for p in pts) for a in range(3)]
    high = [max(p[a] for p in pts) for a in range(3)]
    extent = [high[a] - low[a] for a in range(3)]
    if not all(math.isfinite(x) for x in extent):
        raise ValueError('OBJ extent overflow')
    scale = max(extent)
    if not scale or min(extent) <= scale * 1e-8:
        raise ValueError('OBJ is flat or has zero extent')
    # Detect oblique planes too; bbox thickness alone does not prove volume.
    delta = lambda p, q: tuple(p[a] - q[a] for a in range(3))
    cross = lambda u, v: (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    dot = lambda u, v: sum(u[a]*v[a] for a in range(3))
    origin = pts[0]
    axis = delta(max(pts, key=lambda p: dot(delta(p, origin), delta(p, origin))), origin)
    normal = max((cross(axis, delta(p, origin)) for p in pts), key=lambda n: dot(n, n))
    norm = math.sqrt(dot(normal, normal))
    if not norm or max(abs(dot(normal, delta(p, origin))) / norm for p in pts) <= scale * 1e-8:
        raise ValueError('OBJ referenced surface is coplanar')
    return {'vertex_count': len(points), 'referenced_vertex_count': len(used),
            'face_count': len(faces), 'bbox_min_native': low, 'bbox_max_native': high,
            'extent_native': extent, 'noncoplanar_surface': True,
            'units': 'unknown', 'shape_fidelity': 'not_tested',
            'topology_and_texture_validation': 'not_tested'}


def prepare(bundle_path, image_path, reference, license_note, backend):
    out = Path(make_unique_run_dir('image_intake'))
    result = {'status': 'conflict', 'generation': 'not_tested', 'physics': 'not_tested',
              'readback': 'not_tested', 'render': 'not_tested', 'human_webrtc': 'not_tested'}
    code = 4
    try:
        bundle_raw = bundle_path.read_bytes()
        write_json(str(out / 'registry_snapshot.json'), {
            'capabilities': json.loads((ROOT / 'contracts/workflow/capabilities.json').read_text()),
            'tasks': json.loads((ROOT / 'contracts/workflow/task_requirements.json').read_text())})
        registry = json.loads((out / 'registry_snapshot.json').read_text())
        (out / 'bundle.json').write_bytes(bundle_raw)
        preflight = evaluate(json.loads(bundle_raw), registry['capabilities']['capabilities'], registry['tasks']['tasks'])
        write_json(str(out / 'preflight.json'), preflight)
        if preflight['status'] != 'ready_for_planning':
            result.update(status=preflight['status'], reason='workflow_preflight_not_ready')
            code = {'conflict': 4, 'unsupported': 3, 'needs_input': 2}[preflight['status']]
        else:
            bundle = json.loads(bundle_raw)
            if preflight['required_behaviors'] != ['rigid_contact'] or bundle['task_brief']['intended_task'] != 'move' or len(bundle['assembly_graph']['parts']) != 1 or bundle['assembly_graph']['interfaces']:
                raise ValueError('initial image scope requires one whole-object rigid move task')
            cards = {p['id']: p for p in bundle['parameter_cards']}
            for name, unit in [('length', 'm'), ('mass', 'kg')]:
                card = cards.get(name)
                if card is None or card['value'] is None or card['unit'] != unit or card['value'] <= 0:
                    raise ValueError('positive metric length and mass required for image task')
            if not reference.strip() or not license_note.strip():
                raise ValueError('image reference and license declaration required')
            if image_path.stat().st_size > MAX_FILE:
                raise ValueError('image exceeds intake budget')
            raw = image_path.read_bytes()
            info = png_info(raw)
            (out / 'input').mkdir()
            target = out / 'input/drill.png'
            target.write_bytes(raw)
            request = {'schema': 'parcel_forge.image_request/1', 'bundle_sha256': sha256_file(str(out / 'bundle.json')),
                       'image': {'path': 'input/drill.png', 'sha256': hashlib.sha256(raw).hexdigest(),
                                 'reference': reference, 'license_declaration': license_note,
                                 'license_review': 'not_tested', **info},
                       'provider': {'name': 'TripoSR' if backend == 'TRIPOSR' else 'EmbodiedGen',
                                    'commit': TRIPOSR_PIN if backend == 'TRIPOSR' else PIN, 'backend': backend,
                                    'seed': 0, 'total_attempts': 1},
                       'scope': 'standalone_rigid_drill', 'generation_authorized': False,
                       'code_sha256': {str(p.relative_to(ROOT)): sha256_file(str(p)) for p in
                                       (Path(__file__), ROOT / 'scripts/pf-image-task',
                                        ROOT / 'src/parcel_forge/workflow/preflight.py')},
                       'registry_snapshot_sha256': sha256_file(str(out / 'registry_snapshot.json'))}
            write_json(str(out / 'request.json'), request)
            # An inspectable command, never an implicit model invocation.
            command = [str(ROOT / '.venvs/embodiedgen/bin/img3d-cli'), '--image_path', str(target),
                       '--output_root', str(out / 'provider/raw'), '--image3d_model', backend,
                       '--seed', '0', '--n_retry', '1', '--asset_type', 'cordless drill']
            if backend == 'TRIPOSR':
                command = [str(ROOT / 'scripts/pf-image-generate'), '--run', str(out)]
            write_json(str(out / 'provider_command.json'), {'command': command, 'execution': 'not_tested',
                                                          'prerequisite': 'isolated_backend_qualification'})
            result.update(status='prepared', reason='input_only_not_model_execution')
            code = 0
    except (OSError, ValueError, TypeError, KeyError, OverflowError, zlib.error) as exc:
        result['reason'] = str(exc)
    result['exit_code'] = code
    write_json(str(out / 'result.json'), result)
    return out, result


def collect(source_run, artifacts):
    out = Path(make_unique_run_dir('image_artifact_handoff'))
    result = {'status': 'conflict', 'generation': 'not_tested', 'physics': 'not_tested',
              'readback': 'not_tested', 'render': 'not_tested', 'human_webrtc': 'not_tested'}
    code = 4
    try:
        source = source_run.resolve()
        if source.parent != (ROOT / 'runs').resolve():
            raise ValueError('source must be an immediate project run directory')
        request_raw = (source / 'request.json').read_bytes()
        request = json.loads(request_raw)
        if json.loads((source / 'result.json').read_text()).get('status') != 'prepared':
            raise ValueError('source intake not prepared')
        if request.get('schema') != 'parcel_forge.image_request/1':
            raise ValueError('unsupported request schema')
        if request['image']['path'] != 'input/drill.png':
            raise ValueError('invalid image snapshot path')
        if sha256_file(str(source / 'bundle.json')) != request['bundle_sha256'] or sha256_file(str(source / request['image']['path'])) != request['image']['sha256']:
            raise ValueError('source input hash mismatch')
        if artifacts.is_symlink() or not artifacts.is_dir():
            raise ValueError('artifacts must be a real directory')
        artifact_root = artifacts.resolve()
        if artifact_root == out.resolve() or artifact_root in out.resolve().parents:
            raise ValueError('artifact source cannot contain the destination run')
        files = sorted(artifacts.rglob('*'))
        if any(p.is_symlink() or not (p.is_file() or p.is_dir()) for p in files):
            raise ValueError('symlinks or special artifact files forbidden')
        sizes = [p.stat().st_size for p in files if p.is_file()]
        if len(sizes) > 2000 or sum(sizes) > 256 * 1024 * 1024 or any(n > MAX_FILE for n in sizes):
            raise ValueError('artifact snapshot exceeds budget')
        (out / 'request.json').write_bytes(request_raw)
        shutil.copytree(artifacts, out / 'provider/raw')
        snapshot = out / 'provider/raw'
        meshes = sorted(snapshot.rglob('*.obj'))
        if not meshes:
            raise ValueError('initial handoff requires OBJ (GLB parser not implemented)')
        stats = {str(p.relative_to(snapshot)): obj_info(p) for p in meshes}
        hashes = {str(p.relative_to(snapshot)): sha256_file(str(p)) for p in snapshot.rglob('*') if p.is_file()}
        result.update(status='artifact_handoff_checked', source_run=source.name,
                      source_request_sha256=hashlib.sha256(request_raw).hexdigest(),
                      artifacts_sha256=hashes, obj_metrics=stats,
                      note='External artifacts; no proof of image-to-model causality or shape fidelity. No USD/physics pass.')
        code = 0
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        result['reason'] = str(exc)
    result['exit_code'] = code
    write_json(str(out / 'result.json'), result)
    return out, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('prepare', help='Validate/snapshot input; never launch provider')
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--image', type=Path, required=True)
    p.add_argument('--reference', required=True)
    p.add_argument('--license-note', required=True)
    p.add_argument('--backend', choices=['TRELLIS', 'SAM3D', 'TRIPOSR'], default='TRELLIS')
    p = sub.add_parser('collect', help='Snapshot external OBJ artifacts; no physics claim')
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--artifacts', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'prepare':
        out, result = prepare(args.bundle, args.image, args.reference, args.license_note, args.backend)
    else:
        out, result = collect(args.run, args.artifacts)
    print(json.dumps({'run': str(out), **result}, ensure_ascii=False, indent=2))
    return result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())

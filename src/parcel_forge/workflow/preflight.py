"""Offline bundle validation; never grants physics pass or launches providers."""
import argparse
import json
import math
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
FIELDS = {
    'root': {'schema', 'asset_id', 'task_brief', 'assembly_graph', 'parameter_cards', 'asset_contract', 'capability_report', 'validation_plan'},
    'task_brief': {'intended_task', 'initial_state', 'base_mode', 'success_observations', 'required_behaviors'},
    'assembly_graph': {'parts', 'interfaces'},
    'part': {'id', 'frame', 'material'},
    'interface': {'id', 'a', 'b', 'kind'},
    'parameter': {'id', 'value', 'unit', 'required', 'provenance', 'source', 'confidence', 'conditions', 'derivation'},
    'asset_contract': {'passive', 'forbidden_simplifications', 'runtime_requirements', 'approximation_scope'},
    'capability_report': {'status'},
    'validation_plan': {'required_checks', 'check_status'},
}
PROVENANCE = {'user_given', 'measured', 'manufacturer', 'literature_matched', 'literature_analogy', 'derived', 'assumed', 'unknown'}


def evaluate(bundle, capabilities, tasks):
    errors, missing, gaps = [], [], []

    def error(path, reason):
        errors.append({'path': path, 'reason': reason})

    def obj(value, kind, path):
        if not isinstance(value, dict):
            error(path, 'expected_object'); return {}
        if set(value) != FIELDS[kind]:
            error(path, 'missing_or_unknown_fields')
        return value

    def strings(value, path):
        if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
            error(path, 'expected_string_list'); return []
        if len(value) != len(set(value)):
            error(path, 'duplicate_values')
        return value

    def finite(value, path):
        if isinstance(value, float) and not math.isfinite(value): error(path, 'not_finite')
        if isinstance(value, dict):
            for k, v in value.items(): finite(v, path + '/' + str(k))
        if isinstance(value, list):
            for i, v in enumerate(value): finite(v, path + '/' + str(i))

    b = obj(bundle, 'root', '/')
    finite(b, '')
    if b.get('schema') != 'parcel_forge.workflow_bundle/1': error('/schema', 'unsupported_version')
    if not isinstance(b.get('asset_id'), str) or not b.get('asset_id'): error('/asset_id', 'expected_nonempty_string')
    task = obj(b.get('task_brief'), 'task_brief', '/task_brief')
    behavior = strings(task.get('required_behaviors'), '/task_brief/required_behaviors')
    task_name = task.get('intended_task')
    if not isinstance(task_name, str) or task_name not in tasks:
        error('/task_brief/intended_task', 'unknown_task'); task_required = []
    else: task_required = tasks[task_name]
    required = sorted(set(behavior + task_required))
    strings(task.get('success_observations'), '/task_brief/success_observations')
    if not task.get('success_observations'): error('/task_brief/success_observations', 'empty_success_definition')
    if task.get('base_mode') not in ('free', 'fixed'): error('/task_brief/base_mode', 'invalid_base_mode')
    if task_name in ('move', 'open_and_extract', 'open_unwrap_and_extract') and task.get('base_mode') != 'free':
        error('/task_brief/base_mode', 'robot_prop_must_be_movable')
    initial = task.get('initial_state')
    if not isinstance(initial, str) or not initial: error('/task_brief/initial_state', 'expected_nonempty_string')
    elif initial == 'unconfirmed': missing.append('/task_brief/initial_state')
    graph = obj(b.get('assembly_graph'), 'assembly_graph', '/assembly_graph')
    part_ids = set()
    for kind, key in [('part', 'parts'), ('interface', 'interfaces')]:
        values = graph.get(key)
        if not isinstance(values, list): error('/assembly_graph/' + key, 'expected_list'); continue
        seen = set()
        if key == 'parts' and not values: error('/assembly_graph/parts', 'empty_assembly')
        for i, value in enumerate(values):
            path = '/assembly_graph/' + key + '/' + str(i)
            item = obj(value, kind, path)
            ident = item.get('id')
            if not isinstance(ident, str) or not ident: error(path + '/id', 'invalid_id')
            elif ident in seen: error(path + '/id', 'duplicate_id')
            else: seen.add(ident)
            if key == 'parts':
                for field in ('frame', 'material'):
                    if not isinstance(item.get(field), str) or not item.get(field): error(path + '/' + field, 'invalid_string')
            else:
                if item.get('a') not in part_ids or item.get('b') not in part_ids or item.get('a') == item.get('b'):
                    error(path, 'invalid_interface_reference')
                if not isinstance(item.get('kind'), str) or not item.get('kind'): error(path + '/kind', 'invalid_string')
        if key == 'parts': part_ids = seen
    parameters = b.get('parameter_cards')
    seen = set()
    if not isinstance(parameters, list): error('/parameter_cards', 'expected_list'); parameters = []
    for i, value in enumerate(parameters):
        path = '/parameter_cards/' + str(i)
        p = obj(value, 'parameter', path)
        ident = p.get('id')
        if not isinstance(ident, str) or not ident: error(path + '/id', 'invalid_id')
        elif ident in seen: error(path + '/id', 'duplicate_id')
        else: seen.add(ident)
        if type(p.get('required')) is not bool: error(path + '/required', 'expected_boolean')
        if not isinstance(p.get('unit'), str) or not p.get('unit'): error(path + '/unit', 'missing_unit')
        if not isinstance(p.get('provenance'), str) or p.get('provenance') not in PROVENANCE: error(path + '/provenance', 'invalid_provenance')
        if p.get('required') and p.get('value') is None: missing.append(path + '/value')
        if p.get('value') is not None and p.get('provenance') == 'unknown': error(path, 'value_without_provenance')
        if isinstance(p.get('provenance'), str) and p.get('provenance') in ('measured', 'manufacturer', 'literature_matched', 'literature_analogy') and not p.get('source'):
            error(path + '/source', 'source_required')
        if p.get('provenance') == 'derived' and not p.get('derivation'): error(path + '/derivation', 'derivation_required')
        if not isinstance(p.get('conditions'), dict): error(path + '/conditions', 'expected_object')
        val = p.get('value')
        if val is not None and (type(val) not in (int, float) or not math.isfinite(val)):
            error(path + '/value', 'expected_finite_scalar')
        if p.get('unit') not in ('m', 'kg', 'kg/m2', 'kg/m3', 'N', 'N*m', 'N*m/rad', 'N*m*s/rad', 'rad', 's', '1', 'Pa', 'N/m'):
            error(path + '/unit', 'unsupported_unit')
        if p.get('confidence') not in ('high', 'medium', 'low', 'unknown'):
            error(path + '/confidence', 'invalid_confidence')
        if isinstance(val, (int, float)) and not isinstance(val, bool) and any(word in str(ident) for word in ('mass', 'thickness', 'length', 'width', 'height')) and val <= 0:
            error(path + '/value', 'positive_physical_quantity_required')
        source = p.get('source')
        if source is not None:
            if not isinstance(source, dict) or set(source) != {'reference', 'locator', 'accessed_at', 'applicability'}:
                error(path + '/source', 'source_card_required')
            elif any(not isinstance(x, str) or not x for x in source.values()):
                error(path + '/source', 'empty_source_field')

    contract = obj(b.get('asset_contract'), 'asset_contract', '/asset_contract')
    if contract.get('passive') is not True: error('/asset_contract/passive', 'passive_asset_required')
    forbidden = strings(contract.get('forbidden_simplifications'), '/asset_contract/forbidden_simplifications')
    for rule in ('commanded_pose', 'disable_required_collision', 'remove_required_behavior'):
        if rule not in forbidden: error('/asset_contract/forbidden_simplifications', 'missing_protection:' + rule)
    if task_name == 'unwrap' and 'closed_shell_for_unwrap' not in forbidden:
        error('/asset_contract/forbidden_simplifications', 'closed_shell_not_equivalent')
    runtime = strings(contract.get('runtime_requirements'), '/asset_contract/runtime_requirements')
    plan = obj(b.get('validation_plan'), 'validation_plan', '/validation_plan')
    selected = strings(plan.get('required_checks'), '/validation_plan/required_checks')
    expected = ['structure.units', 'structure.references'] + ['behavior.' + x for x in required]
    if task.get('base_mode') == 'free': expected.append('structure.mobility')
    for check in expected:
        if check not in selected: error('/validation_plan/required_checks', 'missing_required_check:' + check)
    known = {'structure.units', 'structure.references', 'structure.mobility'} | {'behavior.' + x for x in capabilities}
    for check in selected:
        if check not in known: gaps.append('check:' + check)
    if plan.get('check_status') != 'planned': error('/validation_plan/check_status', 'preflight_cannot_claim_execution')
    obj(b.get('capability_report'), 'capability_report', '/capability_report')
    for name in required:
        c = capabilities.get(name)
        if c is None or c.get('implementation') != 'implemented': gaps.append(name)
        elif c.get('runtime_required') and name not in runtime: error('/asset_contract/runtime_requirements', 'missing_runtime:' + name)
    dimensions = {x.get('id'): x.get('value') for x in parameters if isinstance(x, dict) and isinstance(x.get('id'), str)}
    for axis in ('length', 'width'):
        outer, inner = dimensions.get('payload_' + axis), dimensions.get('carton_inner_' + axis)
        if type(outer) in (int, float) and type(inner) in (int, float) and outer >= inner:
            error('/parameter_cards', 'payload_does_not_fit:' + axis)
    status = 'conflict' if errors else 'unsupported' if gaps else 'needs_input' if missing else 'ready_for_planning'
    return {'status': status, 'errors': errors, 'missing_inputs': missing, 'capability_gaps': sorted(set(gaps)),
            'required_behaviors': required, 'selected_checks': expected, 'generation_authorized': False,
            'clarifications': [{'path': x, 'reason': 'required_value_unknown'} for x in missing],
            'physics_execution': 'not_tested', 'human_webrtc': 'not_tested'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for n in range(10000):
        out = ROOT / 'runs' / (stamp + '_workflow_preflight' + ('' if n == 0 else '-' + str(n)))
        try: out.mkdir(); break
        except FileExistsError: continue
    else: raise RuntimeError('run allocation exhausted')
    try:
        raw = args.bundle.read_bytes()
        (out / 'input.json').write_bytes(raw)
        caps = json.loads((ROOT / 'contracts/workflow/capabilities.json').read_text())['capabilities']
        tasks = json.loads((ROOT / 'contracts/workflow/task_requirements.json').read_text())['tasks']
        result = evaluate(json.loads(raw), caps, tasks)
    except (ValueError, OSError, TypeError) as exc:
        result = {'status': 'conflict', 'errors': [{'reason': str(exc)}], 'generation_authorized': False,
                  'physics_execution': 'not_tested', 'human_webrtc': 'not_tested'}
    code = {'ready_for_planning': 0, 'needs_input': 2, 'unsupported': 3, 'conflict': 4}[result['status']]
    result['exit_code'] = code
    (out / 'preflight.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'run': str(out), **result}, ensure_ascii=False, indent=2))
    return code


if __name__ == '__main__':
    raise SystemExit(main())

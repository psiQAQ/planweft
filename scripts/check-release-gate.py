#!/usr/bin/env python3
"""Policy-driven schema 3 gate for immutable PlanWeft stable archives."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parents[1]
HOSTS = ('codex', 'claude', 'pi', 'opencode', 'dsh')
OTHER_HOSTS = ('hermes', 'cursor', 'gemini', 'copilot', 'mastracode',
               'kiro', 'continue', 'factory', 'codebuddy', 'agents')
LOCAL_CHECKS = ('exact_artifact', 'native_lifecycle', 'skill_loading', 'offline_controls',
                'context_injection', 'recovery', 'stopping', 'permissions',
                'model_maintenance', 'cold_read')
REMOTE_CHECKS = ('remote_lifecycle', 'remote_session', 'native_channels')
MODEL_CHECKS = ('context_injection', 'recovery', 'stopping', 'model_maintenance',
                'cold_read')
WORKFLOWS = {
    'codex_explicit_maintenance_cold_read': ('codex', 'explicit', 'required'),
    'pi_explicit_maintenance_cold_read': ('pi', 'explicit', 'evidence_based'),
    'pi_auto_maintenance_cold_read': ('pi', 'auto', 'evidence_based'),
}
SCENARIOS = {
    'exact_artifact': ('archive_bytes', 'installed_contents', 'runtime_dependencies'),
    'native_lifecycle': ('install', 'update', 'rollback', 'remove', 'reinstall',
                         'fixture_add_modify_delete', 'partial_failure_recovery'),
    'skill_loading': ('single_main_skill', 'actual_skill_read'),
    'offline_controls': ('default_advisory', 'explicit_disable',
                         'continuation_cap', 'continuation_stall'),
    'context_injection': ('context_delivery', 'reminder_deduplication'),
    'recovery': ('fresh_session_project_files',),
    'model_maintenance': ('automatic_adoption', 'authorized_file_access',
                          'authorized_environment_access', 'regression_tests',
                          'approved_requirements', 'single_state_source', 'accurate_records'),
    'cold_read': ('goal_and_next_action', 'historical_results_and_limits'),
    'remote_lifecycle': ('candidate_to_release', 'release_to_candidate',
                         'candidate_to_release_again', 'uninstall'),
    'remote_session': ('fresh_session_native_loading',),
    'native_channels': ('native_install', 'native_update', 'native_remove'),
}
STATUSES = ('Passed', 'Failed', 'Inconclusive', 'Not Run')
STATUS_RANK = {'Passed': 0, 'Not Run': 1, 'Inconclusive': 2, 'Failed': 3}
TIERS = ('required', 'evidence_based', 'experimental')


def expected_scenarios(host, check):
    if check == 'stopping':
        return (('normal_stop', 'explicit_continuation', 'continuation_limit') if host == 'pi'
                else ('normal_stop', 'explicit_continuation', 'gate_cap', 'gate_stall',
                      'gate_cap_disabled', 'gate_stall_disabled'))
    if check == 'permissions':
        values = ['readonly_disabled', 'project_isolation', 'user_change_protection',
                  'duplicate_hooks']
        values.append('package_approval' if host == 'pi' else 'native_permission_denial')
        if host == 'codex':
            values += ['untrusted_hooks', 'persisted_hook_trust']
        return tuple(values)
    return SCENARIOS[check]


def expected_core_rule(host, check, scenario):
    """Return the frozen 0.4.0 minimum contract, not a permissive default."""
    check_tier = ('experimental' if check in {'context_injection', 'recovery', 'stopping',
                                              'model_maintenance', 'cold_read'}
                  else 'required')
    tier = check_tier
    reusable = True
    if check == 'exact_artifact':
        reusable = False
    if check == 'native_lifecycle' and scenario in {'install', 'remove'}:
        reusable = False
    if check == 'skill_loading' and scenario == 'actual_skill_read':
        reusable = False
    if check == 'permissions' and scenario == 'user_change_protection':
        reusable = False
    if check in REMOTE_CHECKS and scenario in {
            'uninstall', 'fresh_session_native_loading', 'native_install', 'native_remove'}:
        reusable = False
    return check_tier, {'tier': tier, 'reusable': reusable}


def file_sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_policy(path):
    policy = json.loads(path.read_text())
    if policy.get('schema_version') != 1 or policy.get('acceptance_schema_version') != 3:
        raise ValueError('Unsupported support policy schema')
    if policy.get('version') != '0.4.0' or policy.get('statuses') != list(STATUSES) or policy.get('tiers') != list(TIERS):
        raise ValueError('Support policy vocabulary differs')
    if set(policy.get('core', {})) != set(HOSTS):
        raise ValueError('Support policy host set differs')
    for host in HOSTS:
        checks = policy['core'][host]
        if set(checks) != set(LOCAL_CHECKS + REMOTE_CHECKS):
            raise ValueError('Support policy check set differs: ' + host)
        for check, item in checks.items():
            if set(item) != {'tier', 'phase', 'scenarios'} or item['tier'] not in TIERS:
                raise ValueError('Invalid support policy item: ' + host + '/' + check)
            phase = 'promotion' if check in REMOTE_CHECKS else 'prepublication'
            if item['phase'] != phase or set(item['scenarios']) != set(expected_scenarios(host, check)):
                raise ValueError('Support policy scenarios differ: ' + host + '/' + check)
            for scenario, rule in item['scenarios'].items():
                if set(rule) != {'tier', 'reusable'} or rule['tier'] not in TIERS or type(rule['reusable']) is not bool:
                    raise ValueError('Invalid support policy scenario: ' + host + '/' + check + '/' + scenario)
                expected_tier, expected_rule = expected_core_rule(host, check, scenario)
                if item['tier'] != expected_tier or rule != expected_rule:
                    raise ValueError('Support policy weakens frozen contract: ' + host + '/' + check + '/' + scenario)
    if set(policy.get('workflows', {})) != set(WORKFLOWS):
        raise ValueError('Support policy workflow set differs')
    for name, (host, mode, tier) in WORKFLOWS.items():
        item = policy['workflows'][name]
        if (set(item) != {'host', 'adoption_mode', 'tier', 'phase', 'scenarios'}
                or (item['host'], item['adoption_mode'], item['tier'], item['phase']) !=
                   (host, mode, tier, 'prepublication')
                or set(item['scenarios']) != {'maintenance', 'independent_cold_read', 'scope_compliance'}):
            raise ValueError('Support policy workflow differs: ' + name)
        if any(set(rule) != {'tier', 'reusable'} or rule != {'tier': tier, 'reusable': False}
               for rule in item['scenarios'].values()):
            raise ValueError('Invalid support workflow scenario: ' + name)
    reviews = policy.get('independent_review', {})
    if set(reviews) != {'prepublication', 'promotion'}:
        raise ValueError('Independent review phases differ')
    for phase, rule in reviews.items():
        if rule != {'tier': 'required', 'phase': phase, 'reusable': False}:
            raise ValueError('Independent review policy differs: ' + phase)
    distributions = policy.get('experimental_distributions', {})
    if set(distributions) != set(OTHER_HOSTS) or any(v != {'tier': 'experimental'} for v in distributions.values()):
        raise ValueError('Experimental distribution policy differs')
    return policy


def read_attachment(root, record, label, forbidden=()):
    if not isinstance(record, dict) or not isinstance(record.get('evidence'), str):
        raise ValueError('Evidence reference missing: ' + label)
    relative = Path(record['evidence'])
    attachment = (root / relative).resolve()
    if (relative.is_absolute() or '..' in relative.parts or attachment == root
            or root not in attachment.parents):
        raise ValueError('Evidence must remain inside evidence root: ' + label)
    if attachment in forbidden:
        raise ValueError('Evidence cannot reference itself: ' + label)
    if not attachment.is_file():
        raise ValueError('Evidence attachment missing: ' + label)
    raw = attachment.read_bytes()
    if record.get('sha256') != hashlib.sha256(raw).hexdigest():
        raise ValueError('Evidence attachment digest differs: ' + label)
    return raw, attachment


def aggregate_status(scenarios):
    values = [item.get('status') for item in scenarios.values()]
    if not values or any(value not in STATUSES for value in values):
        raise ValueError('Scenario status missing or invalid')
    return max(values, key=STATUS_RANK.__getitem__)


def validate_nonpass(item, rule, label):
    status = item.get('status')
    if status == 'Not Run' and (not isinstance(item.get('reason'), str) or not item['reason']):
        raise ValueError('Not Run requires reason: ' + label)
    if status in {'Failed', 'Inconclusive'} and rule['tier'] != 'required':
        limit = item.get('public_limit_id')
        if not isinstance(limit, str) or not re.fullmatch(r'LIMIT-[A-Z0-9-]+', limit):
            raise ValueError('Non-blocking result requires public limit ID: ' + label)


def validate_reuse(root, item, rule, label, version, digest, forbidden, attestation):
    kind = item.get('evidence_type')
    if kind not in {'fresh', 'reused'}:
        raise ValueError('Evidence type missing: ' + label)
    if kind == 'fresh':
        if 'reuse' in item:
            raise ValueError('Fresh evidence cannot carry reuse metadata: ' + label)
        return
    if not rule['reusable']:
        raise ValueError('Non-reusable scenario cannot use reused evidence: ' + label)
    reuse = item.get('reuse')
    keys = {'source_version', 'source_npm_sha256', 'target_version', 'target_npm_sha256',
            'manifest_diff', 'affected_checks', 'reviewer'}
    if not isinstance(reuse, dict) or set(reuse) != keys:
        raise ValueError('Reused evidence binding missing: ' + label)
    if (reuse['target_version'] != version or reuse['target_npm_sha256'] != digest
            or not isinstance(reuse['source_version'], str)
            or not re.fullmatch(r'[0-9a-f]{64}', reuse['source_npm_sha256'])
            or (reuse['source_version'], reuse['source_npm_sha256']) == (version, digest)
            or not isinstance(reuse['reviewer'], str) or not reuse['reviewer']
            or not isinstance(reuse['affected_checks'], list)
            or any(not isinstance(value, str) or not value for value in reuse['affected_checks'])
            or label in reuse['affected_checks']):
        raise ValueError('Reused evidence package or review binding differs: ' + label)
    raw, _ = read_attachment(root, reuse['manifest_diff'], label + '/manifest-diff',
                             forbidden + (attestation,))
    manifest = json.loads(raw)
    if (set(manifest) != {'schema_version', 'source_version', 'source_npm_sha256',
                          'target_version', 'target_npm_sha256', 'changed_files',
                          'affected_checks', 'reviewer'}
            or manifest['schema_version'] != 1
            or manifest['source_version'] != reuse['source_version']
            or manifest['source_npm_sha256'] != reuse['source_npm_sha256']
            or manifest['target_version'] != version
            or manifest['target_npm_sha256'] != digest
            or manifest['affected_checks'] != reuse['affected_checks']
            or manifest['reviewer'] != reuse['reviewer']
            or not isinstance(manifest['changed_files'], list)
            or not manifest['changed_files']):
        raise ValueError('Manifest diff binding differs: ' + label)
    for change in manifest['changed_files']:
        if (not isinstance(change, dict) or set(change) != {'path', 'before_sha256', 'after_sha256'}
                or not isinstance(change['path'], str)):
            raise ValueError('Manifest diff file entry differs: ' + label)
        path = Path(change['path'])
        hashes = (change['before_sha256'], change['after_sha256'])
        if (path.is_absolute() or '..' in path.parts or not path.parts
                or any(value is not None and not re.fullmatch(r'[0-9a-f]{64}', value) for value in hashes)
                or hashes[0] == hashes[1]):
            raise ValueError('Manifest diff file binding differs: ' + label)


def validate_record(root, record, rules, label, binding, version, digest, forbidden, model=False):
    if not isinstance(record, dict) or record.get('status') not in STATUSES:
        raise ValueError('Acceptance record missing or invalid: ' + label)
    if record.get('evidence_type') != 'fresh' or 'reuse' in record:
        raise ValueError('Aggregate attestation must be fresh: ' + label)
    raw, attachment = read_attachment(root, record, label, forbidden)
    observed = json.loads(raw)
    expected = {'status': record['status'], 'version': version, 'npm_sha256': digest, **binding}
    if any(observed.get(key) != value for key, value in expected.items()):
        raise ValueError('Evidence attachment binding differs: ' + label)
    details = observed.get('observations')
    if not isinstance(details, dict) or set(details.get('scenarios', {})) != set(rules):
        raise ValueError('Evidence scenarios differ: ' + label)
    scenarios = details['scenarios']
    try:
        aggregate = aggregate_status(scenarios)
    except ValueError as error:
        raise ValueError(str(error) + ': ' + label) from error
    if aggregate != record['status']:
        raise ValueError('Aggregate status differs from scenarios: ' + label)
    for scenario, rule in rules.items():
        item = scenarios[scenario]
        scenario_label = label + '/' + scenario
        validate_nonpass(item, rule, scenario_label)
        artifacts = item.get('artifacts', [])
        if item['status'] != 'Not Run' and (not isinstance(artifacts, list) or not artifacts):
            raise ValueError('Executed scenario requires raw attachments: ' + scenario_label)
        if not isinstance(artifacts, list):
            raise ValueError('Scenario artifacts differ: ' + scenario_label)
        for artifact in artifacts:
            _, path = read_attachment(root, artifact, scenario_label, forbidden + (attachment,))
            if path == attachment:
                raise ValueError('Scenario cannot cite its own attestation: ' + scenario_label)
        validate_reuse(root, item, rule, scenario_label, version, digest,
                       forbidden, attachment)
    if model and record['status'] != 'Not Run':
        required = ('image', 'cli_version', 'model', 'runner_sha256', 'session_id')
        if (details.get('kind') != 'actual-host-model'
                or not all(isinstance(details.get(key), str) and details[key] for key in required)
                or details.get('external_memory') is not False):
            raise ValueError('Actual host/model provenance missing: ' + label)
    return scenarios, details


def result_rows(evidence, phase='promotion'):
    rows = []
    for host in HOSTS:
        for check in LOCAL_CHECKS + REMOTE_CHECKS:
            if phase == 'prepublication' and check in REMOTE_CHECKS:
                continue
            record = evidence['core'][host][check]
            rows.append([host + '/' + check, record['status'], record['sha256']])
    for name in WORKFLOWS:
        record = evidence['workflows'][name]
        rows.append(['workflows/' + name, record['status'], record['sha256']])
    return rows


def result_set_digest(evidence, phase='promotion'):
    return hashlib.sha256(json.dumps(result_rows(evidence, phase), separators=(',', ':')).encode()).hexdigest()


def validate_review(root, phase, record, evidence, policy_digest, version, digest, forbidden):
    rules = {'review': {'tier': 'required', 'reusable': False}}
    scenarios, details = validate_record(
        root, record, rules, 'independent_reviews/' + phase,
        {'check': 'independent_review', 'phase': phase}, version, digest, forbidden)
    expected_hashes = {row[2] for row in result_rows(evidence, phase)}
    if (record['status'] != 'Passed' or scenarios['review']['status'] != 'Passed'
            or not isinstance(details.get('reviewer'), str) or not details['reviewer']
            or set(details.get('reviewed_sha256', [])) != expected_hashes
            or details.get('support_policy_sha256') != policy_digest
            or details.get('npm_sha256') != digest
            or details.get('result_set_sha256') != result_set_digest(evidence, phase)
            or (phase == 'promotion' and details.get('prior_review_sha256') !=
                evidence['independent_reviews']['prepublication']['sha256'])):
        raise ValueError('Independent review does not bind policy, package and all results: ' + phase)


def validate_evidence(archive, package, evidence_path, policy_path, evidence_root, promotion=False):
    policy = load_policy(policy_path)
    evidence = json.loads(evidence_path.read_text())
    digest = file_sha256(archive)
    policy_digest = file_sha256(policy_path)
    if evidence.get('schema_version') != 3:
        raise ValueError('Unsupported acceptance schema')
    if (evidence.get('version') != package['version'] or evidence.get('npm_sha256') != digest
            or evidence.get('support_policy_sha256') != policy_digest):
        raise ValueError('Stable evidence does not identify this package and support policy')
    if (set(evidence.get('core', {})) != set(HOSTS)
            or set(evidence.get('workflows', {})) != set(WORKFLOWS)
            or set(evidence.get('independent_reviews', {})) != {'prepublication', 'promotion'}):
        raise ValueError('Acceptance host, workflow or review set differs')
    root = evidence_root.resolve()
    if not root.is_dir():
        raise ValueError('Evidence root is missing')
    forbidden = (evidence_path.resolve(), policy_path.resolve(), archive.resolve())
    blocking = []
    for host in HOSTS:
        if set(evidence['core'][host]) != set(LOCAL_CHECKS + REMOTE_CHECKS):
            raise ValueError('Acceptance check set differs: ' + host)
        for check in LOCAL_CHECKS + REMOTE_CHECKS:
            label = host + '/' + check
            rule = policy['core'][host][check]
            scenarios, _ = validate_record(
                root, evidence['core'][host][check], rule['scenarios'], label,
                {'host': host, 'check': check}, package['version'], digest, forbidden,
                model=check in MODEL_CHECKS)
            if rule['phase'] == 'prepublication' or promotion:
                blocking += [label + '/' + name for name, item in scenarios.items()
                             if rule['scenarios'][name]['tier'] == 'required'
                             and item['status'] != 'Passed']
    for name, (host, mode, _tier) in WORKFLOWS.items():
        label = 'workflows/' + name
        rule = policy['workflows'][name]
        scenarios, details = validate_record(
            root, evidence['workflows'][name], rule['scenarios'], label,
            {'workflow': name, 'host': host}, package['version'], digest, forbidden, model=True)
        classification = ('supported' if all(item['status'] == 'Passed' for item in scenarios.values())
                          else 'blocked' if rule['tier'] == 'required' else 'experimental')
        pair_ran = all(scenarios[key]['status'] != 'Not Run'
                       for key in ('maintenance', 'independent_cold_read'))
        pair_bound = (isinstance(details.get('maintenance_session_id'), str)
                      and isinstance(details.get('cold_read_session_id'), str)
                      and details['maintenance_session_id'] != details['cold_read_session_id']
                      and isinstance(details.get('output_snapshot_sha256'), str)
                      and details.get('output_snapshot_sha256') == details.get('input_snapshot_sha256'))
        evidence_bound = (details.get('maintenance_evidence_sha256') in
                          {item.get('sha256') for item in scenarios['maintenance'].get('artifacts', [])}
                          and details.get('cold_read_evidence_sha256') in
                          {item.get('sha256') for item in scenarios['independent_cold_read'].get('artifacts', [])}
                          and details.get('maintenance_evidence_sha256') !=
                              details.get('cold_read_evidence_sha256')
                          and details.get('history_available') is False
                          and details.get('plugin_available') is False)
        skill_bound = (details.get('skill_loading_evidence_sha256') ==
                       evidence['core'][host]['skill_loading']['sha256'])
        if (details.get('adoption_mode') != mode or details.get('classification') != classification
                or pair_ran and (not pair_bound or not evidence_bound)
                or (mode == 'explicit' and scenarios['maintenance']['status'] == 'Passed'
                    and (details.get('explicit_skill_read') is not True or not skill_bound))):
            raise ValueError('Workflow classification or cold-read binding differs: ' + label)
        blocking += [label + '/' + scenario for scenario, item in scenarios.items()
                     if rule['scenarios'][scenario]['tier'] == 'required'
                     and item['status'] != 'Passed']
    validate_review(root, 'prepublication', evidence['independent_reviews']['prepublication'],
                    evidence, policy_digest, package['version'], digest, forbidden)
    if promotion:
        validate_review(root, 'promotion', evidence['independent_reviews']['promotion'],
                        evidence, policy_digest, package['version'], digest, forbidden)
    computed = bool(blocking)
    if evidence.get('release_blocking') is not computed:
        raise ValueError('release_blocking differs from policy computation')
    if computed:
        raise ValueError('Release is blocked by: ' + ', '.join(blocking))
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, default=ROOT / 'release/acceptance.json')
    parser.add_argument('--policy', type=Path, default=ROOT / 'release/support-policy.json')
    parser.add_argument('--evidence-root', type=Path, default=ROOT)
    parser.add_argument('--promotion', action='store_true',
                        help='Activate required remote results and promotion review before latest')
    args = parser.parse_args()
    with tarfile.open(args.archive) as archive:
        package = json.load(archive.extractfile('package/package.json'))
    if package['name'] != 'planweft':
        parser.error('Unexpected package')
    if '-' in package['version']:
        if args.promotion:
            parser.error('Candidates cannot be promoted to latest')
        print('Candidate: next only; no stable acceptance claimed')
        return
    if not args.evidence.is_file():
        parser.error('Stable acceptance evidence is missing')
    if not args.policy.is_file():
        parser.error('Stable support policy is missing')
    try:
        validate_evidence(args.archive, package, args.evidence, args.policy,
                          args.evidence_root, args.promotion)
    except (ValueError, OSError, TypeError, AttributeError, KeyError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print('Policy-driven ' + ('promotion' if args.promotion else 'pre-publication') + ' gates passed')


if __name__ == '__main__':
    main()

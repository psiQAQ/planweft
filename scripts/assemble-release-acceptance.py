#!/usr/bin/env python3
"""Assemble deterministic schema-3 acceptance records from reviewed evidence inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parents[1]
HOSTS = ('codex', 'claude', 'pi', 'opencode', 'dsh')
LOCAL_CHECKS = ('exact_artifact', 'native_lifecycle', 'skill_loading', 'offline_controls',
                'context_injection', 'recovery', 'stopping', 'permissions',
                'model_maintenance', 'cold_read')
REMOTE_CHECKS = ('remote_lifecycle', 'remote_session', 'native_channels')
WORKFLOWS = ('codex_explicit_maintenance_cold_read',
             'pi_explicit_maintenance_cold_read', 'pi_auto_maintenance_cold_read')
RANK = {'Passed': 0, 'Not Run': 1, 'Inconclusive': 2, 'Failed': 3}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def safe_repo_path(value):
    relative = Path(value)
    target = (ROOT / relative).resolve()
    if (relative.is_absolute() or '..' in relative.parts or ROOT not in target.parents
            or not target.is_file()):
        raise ValueError('Evidence input must be an existing repository file: ' + value)
    return relative.as_posix(), target, digest(target)


def artifact(config, name):
    relative, _, sha = safe_repo_path(config['artifacts'][name])
    return {'evidence': relative, 'sha256': sha}


def aggregate(scenarios):
    return max((item['status'] for item in scenarios.values()), key=RANK.__getitem__)


def not_run(reason):
    return {'status': 'Not Run', 'reason': reason, 'evidence_type': 'fresh', 'artifacts': []}


def fresh(status, evidence, limit=None):
    artifacts = evidence if isinstance(evidence, list) else [evidence]
    item = {'status': status, 'evidence_type': 'fresh', 'artifacts': artifacts}
    if limit:
        item['public_limit_id'] = limit
    return item


def reused(config, version, npm_sha, label, evidence):
    manifest_path, manifest_file, manifest_sha = safe_repo_path(config['artifacts']['manifest_diff'])
    manifest = json.loads(manifest_file.read_text())
    reuse = {
        'source_version': manifest['source_version'],
        'source_npm_sha256': manifest['source_npm_sha256'],
        'target_version': version,
        'target_npm_sha256': npm_sha,
        'manifest_diff': {'evidence': manifest_path, 'sha256': manifest_sha},
        'affected_checks': manifest['affected_checks'],
        'reviewer': manifest['reviewer'],
    }
    if label in reuse['affected_checks']:
        raise ValueError('Affected scenario cannot be reused: ' + label)
    return {'status': 'Passed', 'evidence_type': 'reused', 'artifacts': [evidence], 'reuse': reuse}


def write_attestation(directory, prefix, name, observed):
    raw = json_bytes(observed)
    destination = directory / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    return {'status': observed['status'], 'evidence_type': 'fresh',
            'evidence': (Path(prefix) / name).as_posix(),
            'sha256': hashlib.sha256(raw).hexdigest()}


def actual_model_details(config, host, key):
    source = config['models'][key]
    return {'kind': 'actual-host-model', 'image': source['image'],
            'cli_version': source['cli_version'], 'model': source['model'],
            'runner_sha256': source['runner_sha256'], 'session_id': source['session_id'],
            'external_memory': False}


def core_record(config, policy, host, check, version, npm_sha):
    rules = policy['core'][host][check]['scenarios']
    scenarios = {}
    fresh_runs = artifact(config, 'fresh_runs')
    local_checks = artifact(config, 'local_checks')
    reused_runs = artifact(config, 'reused_runs')
    for scenario, rule in rules.items():
        label = host + '/' + check + '/' + scenario
        if policy['core'][host][check]['phase'] == 'promotion':
            if 'promotion' not in config:
                scenarios[scenario] = not_run('Pending official-registry next publication and promotion validation')
            elif ((check == 'remote_lifecycle' and scenario != 'uninstall')
                  or (check == 'native_channels' and scenario == 'native_update')):
                # The approved stable flow intentionally does not repeat a
                # full RC<->stable registry round trip when runtime/installer
                # or cross-version native update when runtime/installer inputs
                # are unchanged. Bind that semantic reuse to the final archive's
                # deterministic lifecycle plus the parsed RC15 to stable
                # manifest diff, rather than to single-version registry evidence
                # or publication metadata.
                scenarios[scenario] = reused(config, version, npm_sha, label, fresh_runs)
            else:
                run = artifact(config, 'registry_runs')
                proof = artifact(config, 'registry_proof')
                scenarios[scenario] = fresh('Passed', [run, proof])
        elif rule['tier'] == 'experimental':
            scenarios[scenario] = not_run('Not rerun for 0.4.0; experimental historical results remain published separately')
        elif not rule['reusable'] or label in json.loads(
                (ROOT / config['artifacts']['manifest_diff']).read_text())['affected_checks']:
            scenarios[scenario] = fresh('Passed', fresh_runs)
        else:
            scenarios[scenario] = reused(config, version, npm_sha, label, reused_runs)

    details = {'scenarios': scenarios}
    if check == 'offline_controls':
        for scenario in scenarios:
            scenarios[scenario] = fresh('Passed', local_checks)
    if check in {'model_maintenance', 'cold_read'} and host in {'codex', 'pi'}:
        evidence = artifact(config, 'codex_workflow' if host == 'codex' else 'pi_explicit_workflow')
        for scenario in scenarios:
            scenarios[scenario] = fresh('Passed', evidence)
        details.update(actual_model_details(config, host, host + '_' +
                       ('maintenance' if check == 'model_maintenance' else 'cold_read')))
    if check == 'stopping' and host == 'codex':
        evidence = artifact(config, 'codex_gate_pair')
        for scenario in ('gate_cap_disabled', 'gate_cap'):
            scenarios[scenario] = fresh('Failed', evidence, 'LIMIT-CODEX-TRACE-INCOMPLETE')
        details.update(actual_model_details(config, host, 'codex_gate'))
    status = aggregate(scenarios)
    return {'status': status, 'version': version, 'npm_sha256': npm_sha,
            'host': host, 'check': check, 'observations': details}


def workflow_record(config, name, version, npm_sha, skill_sha):
    source = config['workflows'][name]
    maintenance = artifact(config, source['maintenance_artifact'])
    cold = artifact(config, source['cold_artifact'])
    general = artifact(config, source['general_artifact'])
    scenarios = {
        'maintenance': fresh('Passed', maintenance),
        'independent_cold_read': fresh('Passed', cold),
        'scope_compliance': fresh('Passed', general),
    }
    details = {'scenarios': scenarios, **actual_model_details(config, source['host'], source['model_key']),
               'adoption_mode': source['adoption_mode'], 'classification': 'supported',
               'maintenance_session_id': source['maintenance_session_id'],
               'cold_read_session_id': source['cold_read_session_id'],
               'output_snapshot_sha256': source['snapshot_sha256'],
               'input_snapshot_sha256': source['snapshot_sha256'],
               'maintenance_evidence_sha256': maintenance['sha256'],
               'cold_read_evidence_sha256': cold['sha256'],
               'history_available': False, 'plugin_available': False,
               'skill_loading_evidence_sha256': skill_sha}
    if source['adoption_mode'] == 'explicit':
        details['explicit_skill_read'] = True
    return {'status': 'Passed', 'version': version, 'npm_sha256': npm_sha,
            'workflow': name, 'host': source['host'], 'observations': details}


def result_rows(evidence, phase='prepublication'):
    rows = []
    for host in HOSTS:
        checks = LOCAL_CHECKS if phase == 'prepublication' else LOCAL_CHECKS + REMOTE_CHECKS
        for check in checks:
            record = evidence['core'][host][check]
            rows.append([host + '/' + check, record['status'], record['sha256']])
    for name in WORKFLOWS:
        record = evidence['workflows'][name]
        rows.append(['workflows/' + name, record['status'], record['sha256']])
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--attestations-dir', type=Path, required=True)
    parser.add_argument('--evidence-prefix', required=True,
                        help='Repository-relative final location of attestations-dir')
    args = parser.parse_args()
    if args.output.exists() or args.attestations_dir.exists():
        parser.error('Output and attestations directory must be new')
    try:
        config = json.loads(args.config.read_text())
        policy_path = ROOT / 'release/support-policy.json'
        policy = json.loads(policy_path.read_text())
        with tarfile.open(args.archive, 'r:gz') as archive:
            package = json.load(archive.extractfile('package/package.json'))
        version = package['version']
        npm_sha = digest(args.archive)
        if version != policy['version'] or config['version'] != version:
            raise ValueError('Version binding differs')
        evidence = {'schema_version': 3, 'version': version, 'npm_sha256': npm_sha,
                    'support_policy_sha256': digest(policy_path), 'release_blocking': False,
                    'core': {}, 'workflows': {}, 'independent_reviews': {}}
        for host in HOSTS:
            evidence['core'][host] = {}
            for check in LOCAL_CHECKS + REMOTE_CHECKS:
                observed = core_record(config, policy, host, check, version, npm_sha)
                evidence['core'][host][check] = write_attestation(
                    args.attestations_dir, args.evidence_prefix,
                    'core/' + host + '-' + check + '.json', observed)
        for name in WORKFLOWS:
            host = config['workflows'][name]['host']
            observed = workflow_record(config, name, version, npm_sha,
                                       evidence['core'][host]['skill_loading']['sha256'])
            evidence['workflows'][name] = write_attestation(
                args.attestations_dir, args.evidence_prefix, 'workflows/' + name + '.json', observed)
        rows = result_rows(evidence, 'prepublication')
        review_artifact = artifact(config, 'prepublication_review')
        review = config['review']
        review_scenario = (fresh('Passed', review_artifact) if review['status'] == 'Passed'
                           else not_run('Independent pre-publication review is pending'))
        review_details = {'scenarios': {'review': review_scenario},
                          'reviewer': review['reviewer'],
                          'reviewed_sha256': sorted({row[2] for row in rows}),
                          'support_policy_sha256': evidence['support_policy_sha256'],
                          'npm_sha256': npm_sha,
                          'result_set_sha256': hashlib.sha256(json.dumps(
                              rows, separators=(',', ':')).encode()).hexdigest()}
        review_observed = {'status': review['status'], 'version': version,
                           'npm_sha256': npm_sha, 'check': 'independent_review',
                           'phase': 'prepublication', 'observations': review_details}
        evidence['independent_reviews']['prepublication'] = write_attestation(
            args.attestations_dir, args.evidence_prefix,
            'reviews/prepublication.json', review_observed)
        if 'promotion' in config:
            promotion_rows = result_rows(evidence, 'promotion')
            promotion = config['promotion']['review']
            promotion_artifact = artifact(config, 'promotion_review')
            promotion_scenario = (fresh('Passed', promotion_artifact)
                                  if promotion['status'] == 'Passed'
                                  else not_run('Independent promotion review is pending'))
            promotion_details = {
                'scenarios': {'review': promotion_scenario},
                'reviewer': promotion['reviewer'],
                'reviewed_sha256': sorted({row[2] for row in promotion_rows}),
                'support_policy_sha256': evidence['support_policy_sha256'],
                'npm_sha256': npm_sha,
                'result_set_sha256': hashlib.sha256(json.dumps(
                    promotion_rows, separators=(',', ':')).encode()).hexdigest(),
                'prior_review_sha256': evidence['independent_reviews']['prepublication']['sha256'],
            }
            promotion_observed = {'status': promotion['status'], 'version': version,
                                  'npm_sha256': npm_sha, 'check': 'independent_review',
                                  'phase': 'promotion', 'observations': promotion_details}
        else:
            promotion_observed = {'status': 'Not Run', 'version': version, 'npm_sha256': npm_sha,
                                  'check': 'independent_review', 'phase': 'promotion',
                                  'observations': {'scenarios': {'review': not_run(
                                      'Pending official-registry validation and promotion results')}}}
        evidence['independent_reviews']['promotion'] = write_attestation(
            args.attestations_dir, args.evidence_prefix,
            'reviews/promotion.json', promotion_observed)
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError, json.JSONDecodeError) as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(json_bytes(evidence))
    print(json.dumps({'records': len(result_rows(evidence, 'promotion') if 'promotion' in config else rows),
                      'review': review['status'],
                      'output': str(args.output)}))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Configure only a user's own, matching Apple provisioning profile. Never edits a profile."""
import argparse
import datetime
import plistlib
import shutil
import subprocess
from pathlib import Path


def validate_profile(profile, bundle_id, container, environment):
    entitlements = profile.get('Entitlements', {})
    teams = profile.get('TeamIdentifier', [])
    if len(teams) != 1 or teams[0] == '4788TTJ39Y':
        raise ValueError('需要 Pasto 自有开发者团队，不能使用原版厂商团队。')
    team = teams[0]
    if not container.startswith('iCloud.') or 'wiheads' in container.lower():
        raise ValueError('需要 Pasto 自有的 iCloud 容器。')
    app_id = f'{team}.{bundle_id}'
    if entitlements.get('com.apple.application-identifier') != app_id:
        raise ValueError('描述文件的应用标识与当前 Bundle ID 不匹配。')
    if container not in entitlements.get('com.apple.developer.icloud-container-identifiers', []):
        raise ValueError('描述文件未授权此 CloudKit 容器。')
    if 'CloudKit' not in entitlements.get('com.apple.developer.icloud-services', []):
        raise ValueError('描述文件未启用 CloudKit。')
    allowed = entitlements.get('com.apple.developer.icloud-container-environment', [])
    if isinstance(allowed, str):
        allowed = [allowed]
    if environment not in allowed:
        raise ValueError('描述文件未授权此 CloudKit 环境。')
    if profile.get('ExpirationDate', datetime.datetime.min) <= datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None):
        raise ValueError('描述文件已过期。')
    result = {
        'com.apple.application-identifier': app_id,
        'com.apple.developer.team-identifier': team,
        'com.apple.developer.icloud-container-identifiers': [container],
        'com.apple.developer.icloud-services': ['CloudKit'],
        'com.apple.developer.icloud-container-environment': environment,
    }
    for key in ('com.apple.developer.aps-environment', 'aps-environment', 'get-task-allow', 'com.apple.security.get-task-allow'):
        if key in entitlements:
            result[key] = entitlements[key]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--container', required=True)
    parser.add_argument('--environment', choices=['Development', 'Production'], default='Development')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    decoded = subprocess.run(['/usr/bin/security', 'cms', '-D', '-i', str(args.profile)], check=True, capture_output=True)
    profile = plistlib.loads(decoded.stdout)
    info_path = args.bundle / 'Contents/Info.plist'
    info = plistlib.loads(info_path.read_bytes())
    entitlements = validate_profile(profile, info['CFBundleIdentifier'], args.container, args.environment)
    args.output.write_bytes(plistlib.dumps(entitlements))
    info['PastoCloudKitContainerIdentifier'] = args.container
    info_path.write_bytes(plistlib.dumps(info))
    shutil.copyfile(args.profile, args.bundle / 'Contents/embedded.provisionprofile')


if __name__ == '__main__':
    main()

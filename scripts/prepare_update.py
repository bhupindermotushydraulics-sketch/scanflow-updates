"""Verify a signed Scanflow release and publish its update feed. No signing secrets here."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

PACKAGE = 'app.scanflow.mobile.preview'
CERTIFICATE = 'b629eb8b652f49814766f9bc231d7f9539528267c04aaaa4965b48b21ecca4b8'

def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)

def verify_signer_output(output):
    # Android build-tools use both numbered and signature-scheme signer labels.
    digests = re.findall(
        r'^(?:Signer #\d+|V[234](?:\.\d+)? Signer:) certificate SHA-256 digest: ([a-fA-F0-9]{64})\s*$',
        output, re.M)
    if not digests or {v.lower() for v in digests} != {CERTIFICATE}:
        raise ValueError(f'APK does not have the existing Scanflow signing certificate; found {digests}')

def inspect(apk, repo, tag, build_tools):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', repo):
        raise ValueError('Invalid repository')
    if not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+', tag):
        raise ValueError('Use a stable version tag such as v1.3.0')
    signatures = run(str(build_tools / 'apksigner'), 'verify', '--print-certs', str(apk))
    verify_signer_output(signatures)
    badging = run(str(build_tools / 'aapt'), 'dump', 'badging', str(apk))
    package = re.search(r"^package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", badging, re.M)
    minimum = re.search(r"^sdkVersion:'(\d+)'", badging, re.M)
    if not package or not minimum or package[1] != PACKAGE:
        raise ValueError('APK is not the installed Scanflow fleet package')
    if 'application-debuggable' in badging or 'application-testOnly' in badging:
        raise ValueError('Publish the non-debuggable fleet APK')
    if tag != 'v' + package[3]:
        raise ValueError('Release tag must match the APK version name')
    code, sdk, size = int(package[2]), int(minimum[1]), apk.stat().st_size
    if not (1 <= code <= 2147483647 and 26 <= sdk <= 100 and 1024 <= size <= 150*1024*1024):
        raise ValueError('Invalid version, Android requirement or APK size')
    return dict(format=1, packageName=PACKAGE, versionCode=code, versionName=package[3],
                minSdk=sdk, sizeBytes=size, sha256=hashlib.sha256(apk.read_bytes()).hexdigest(),
                apkUrl=f'https://github.com/{repo}/releases/download/{tag}/Scanflow.apk')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--apk', type=Path)
    parser.add_argument('--build-tools', type=Path)
    parser.add_argument('--output', type=Path, default=Path('scanflow-update.json'))
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    # Validate inputs before passing them to gh or using them as API paths.
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', args.repo) or not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+', args.tag):
        raise ValueError('Invalid repository or version tag')
    with tempfile.TemporaryDirectory(prefix='scanflow-release-') as folder:
        work = Path(folder)
        apk = args.apk
        if apk is None:
            release = json.loads(run('gh', 'api', f'repos/{args.repo}/releases/tags/{args.tag}'))
            if release['draft'] or release['prerelease']:
                raise ValueError('Only published stable releases can update devices')
            run('gh', 'release', 'download', args.tag, '--repo', args.repo,
                '--pattern', 'Scanflow.apk', '--dir', folder)
            apk = work / 'Scanflow.apk'
        build_tools = args.build_tools
        if build_tools is None:
            sdk = Path(os.environ.get('ANDROID_HOME') or os.environ['ANDROID_SDK_ROOT'])
            versions = [p for p in (sdk / 'build-tools').iterdir() if re.fullmatch(r'\d+\.\d+\.\d+', p.name)]
            build_tools = max(versions, key=lambda p: tuple(map(int, p.name.split('.'))))
        manifest = inspect(apk.resolve(), args.repo, args.tag, build_tools.resolve())
        content = json.dumps(manifest, indent=2) + '\n'
        args.output.write_text(content)
        if args.publish:
            endpoint = f'repos/{args.repo}/contents/scanflow-update.json'
            existing = None
            try:
                existing = json.loads(run('gh', 'api', endpoint + '?ref=main'))
            except subprocess.CalledProcessError as error:
                if 'HTTP 404' not in error.output:
                    raise
            payload = dict(message=f'Publish verified Scanflow {manifest["versionName"]} update',
                           branch='main', content=base64.b64encode(content.encode()).decode())
            if existing:
                previous = json.loads(base64.b64decode(existing['content']))
                if manifest['versionCode'] < previous['versionCode']:
                    raise ValueError('A newer version is already published')
                if manifest['versionCode'] == previous['versionCode']:
                    if manifest != previous:
                        raise ValueError('Increment versionCode for every changed APK')
                    print('This verified update is already published')
                    return
                payload['sha'] = existing['sha']
            payload_file = work / 'payload.json'
            payload_file.write_text(json.dumps(payload))
            run('gh', 'api', '--method', 'PUT', endpoint, '--input', str(payload_file))
        print(f'Verified Scanflow {manifest["versionName"]} (version code {manifest["versionCode"]})')

if __name__ == '__main__':
    main()

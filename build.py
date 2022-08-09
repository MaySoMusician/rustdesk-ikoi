#!/usr/bin/env python3

import os
import platform
import zipfile
import urllib.request
import shutil
import hashlib
import argparse

windows = platform.platform().startswith('Windows')
osx = platform.platform().startswith('Darwin') or platform.platform().startswith("macOS")
hbb_name = 'rustdesk' + ('.exe' if windows else '')
exe_path = 'target/release/' + hbb_name


def get_version():
    with open("Cargo.toml") as fh:
        for line in fh:
            if line.startswith("version"):
                return line.replace("version", "").replace("=", "").replace('"', '').strip()
    return ''


def parse_rc_features(feature):
    available_features = {
        'IddDriver': {
            'zip_url': 'https://github.com/fufesou/RustDeskIddDriver/releases/download/v0.1/RustDeskIddDriver_x64.zip',
            'checksum_url': 'https://github.com/fufesou/RustDeskIddDriver/releases/download/v0.1'
                            '/RustDeskIddDriver_x64.zip.checksum_md5',
        },
        'PrivacyMode': {
            'zip_url': 'https://github.com/fufesou/RustDeskTempTopMostWindow/releases/download/v0.1'
                       '/TempTopMostWindow_x64.zip',
            'checksum_url': 'https://github.com/fufesou/RustDeskTempTopMostWindow/releases/download/v0.1'
                            '/TempTopMostWindow_x64.zip.checksum_md5',
        }
    }
    apply_features = {}
    if not feature:
        return apply_features
    elif isinstance(feature, str) and feature.upper() == 'ALL':
        return available_features
    elif isinstance(feature, list):
        for feat in feature:
            if isinstance(feat, str) and feat.upper() == 'ALL':
                return available_features
            if feat in available_features:
                apply_features[feat] = available_features[feat]
            else:
                print(f'Unrecognized feature {feat}')
        return apply_features
    else:
        raise Exception(f'Unsupported features param {feature}')


def make_parser():
    parser = argparse.ArgumentParser(description='Build script.')
    parser.add_argument(
        '-f',
        '--feature',
        dest='feature',
        metavar='N',
        type=str,
        nargs='+',
        default='',
        help='Integrate features, windows only.'
             'Available: IddDriver, PrivacyMode. Special value is "ALL" and empty "". Default is empty.')
    parser.add_argument(
        '--hwcodec',
        action='store_true',
        help='Enable feature hwcodec, windows only.'
    )
    return parser


def download_extract_features(features, res_dir):
    for (feat, feat_info) in features.items():
        print(f'{feat} download begin')
        checksum_md5_response = urllib.request.urlopen(feat_info['checksum_url'])
        checksum_md5 = checksum_md5_response.read().decode('utf-8').split()[0]
        download_filename = feat_info['zip_url'].split('/')[-1]
        filename, _headers = urllib.request.urlretrieve(feat_info['zip_url'], download_filename)
        md5 = hashlib.md5(open(filename, 'rb').read()).hexdigest()
        if checksum_md5 != md5:
            raise Exception(f'{feat} download failed')
        print(f'{feat} download end. extract bein')
        zip_file = zipfile.ZipFile(filename)
        zip_list = zip_file.namelist()
        for f in zip_list:
            zip_file.extract(f, res_dir)
        zip_file.close()
        os.remove(download_filename)
        print(f'{feat} extract end')


def get_rc_features(args):
    features = parse_rc_features(args.feature)
    if features:
        print(f'Build with features {list(features.keys())}')
        res_dir = 'resources'
        if os.path.isdir(res_dir) and not os.path.islink(res_dir):
            shutil.rmtree(res_dir)
        elif os.path.exists(res_dir):
            raise Exception(f'Find file {res_dir}, not a directory')
        os.makedirs(res_dir, exist_ok=True)
        download_extract_features(features, res_dir)
    return ['with_rc'] if features else []
    

def get_features(args):
    features = ['inline']
    if windows:
        features.extend(get_rc_features(args))
    if args.hwcodec:
        features.append('hwcodec')
    print("features:", features)
    return features

def main():
    parser = make_parser()
    args = parser.parse_args()

    os.system("cp Cargo.toml Cargo.toml.bk")
    os.system("cp src/main.rs src/main.rs.bk")
    if windows:
        txt = open('src/main.rs', encoding='utf8').read()
        with open('src/main.rs', 'wt', encoding='utf8') as fh:
            fh.write(txt.replace(
                '//#![windows_subsystem', '#![windows_subsystem'))
    if os.path.exists(exe_path):
        os.unlink(exe_path)
    os.system('python3 inline-sciter.py')
    if os.path.isfile('/usr/bin/pacman'):
        os.system('git checkout src/ui/common.tis')
    version = get_version()
    features = ",".join(get_features(args))
    if windows:
        os.system('cargo build --release --features ' + features)
        # os.system('upx.exe target/release/rustdesk.exe')
        # os.system('mv target/release/rustdesk-ikoi.exe target/release/RustDesk.exe')
        pa = os.environ.get('P')
        if pa:
            os.system(f'signtool sign /a /v /p {pa} /debug /f .\\cert.pfx /t http://timestamp.digicert.com  '
                      'target\\release\\rustdesk-ikoi.exe')
        else:
            print('Not signed')
        os.system(f'cp -rf target/release/rustdesk-ikoi.exe rustdesk-{version}-setdown.exe')
    elif os.path.isfile('/usr/bin/pacman'):
        os.system('cargo build --release --features ' + features)
        os.system('git checkout src/ui/common.tis')
        os.system('strip target/release/rustdesk')
        os.system("sed -i 's/pkgver=.*/pkgver=%s/g' PKGBUILD" % version)
        # pacman -S -needed base-devel
        os.system('HBB=`pwd` makepkg -f')
        os.system('mv rustdesk-%s-0-x86_64.pkg.tar.zst rustdesk-%s-manjaro-arch.pkg.tar.zst' % (version, version))
        # pacman -U ./rustdesk.pkg.tar.zst
    elif os.path.isfile('/usr/bin/yum'):
        os.system('cargo build --release --features ' + features)
        os.system('strip target/release/rustdesk')
        os.system("sed -i 's/Version:    .*/Version:    %s/g' rpm.spec" % version)
        os.system('HBB=`pwd` rpmbuild -ba rpm.spec')
        os.system('mv $HOME/rpmbuild/RPMS/x86_64/rustdesk-%s-0.x86_64.rpm ./rustdesk-%s-fedora28-centos8.rpm' % (
            version, version))
        # yum localinstall rustdesk.rpm
    elif os.path.isfile('/usr/bin/zypper'):
        os.system('cargo build --release --features ' + features)
        os.system('strip target/release/rustdesk')
        os.system("sed -i 's/Version:    .*/Version:    %s/g' rpm-suse.spec" % version)
        os.system('HBB=`pwd` rpmbuild -ba rpm-suse.spec')
        os.system('mv $HOME/rpmbuild/RPMS/x86_64/rustdesk-%s-0.x86_64.rpm ./rustdesk-%s-suse.rpm' % (version, version))
        # yum localinstall rustdesk.rpm
    else:
        os.system('cargo bundle --release --features ' + features)
        if osx:
            os.system(
                'strip target/release/bundle/osx/RustDeskIkoiTeachers.app/Contents/MacOS/rustdesk-ikoi')
            os.system(
                'cp libsciter.dylib target/release/bundle/osx/RustDeskIkoiTeachers.app/Contents/MacOS/')
            # https://github.com/sindresorhus/create-dmg
            os.system('/bin/rm -rf *.dmg')
            plist = "target/release/bundle/osx/RustDeskIkoiTeachers.app/Contents/Info.plist"
            txt = open(plist).read()
            with open(plist, "wt") as fh:
                fh.write(txt.replace("</dict>", """
  <key>LSUIElement</key>
  <string>1</string>
</dict>"""))
            pa = os.environ.get('P')
            if pa:
                os.system('''
# buggy: rcodesign sign ... path/*, have to sign one by one
#rcodesign sign --p12-file ~/.p12/rustdesk-developer-id.p12 --p12-password-file ~/.p12/.cert-pass --code-signature-flags runtime ./target/release/bundle/osx/RustDeskIkoiTeachers.app/Contents/MacOS/rustdesk
#rcodesign sign --p12-file ~/.p12/rustdesk-developer-id.p12 --p12-password-file ~/.p12/.cert-pass --code-signature-flags runtime ./target/release/bundle/osx/RustDeskIkoiTeachers.app/Contents/MacOS/libsciter.dylib
#rcodesign sign --p12-file ~/.p12/rustdesk-developer-id.p12 --p12-password-file ~/.p12/.cert-pass --code-signature-flags runtime ./target/release/bundle/osx/RustDeskIkoiTeachers.app
# goto "Keychain Access" -> "My Certificates" for below id which starts with "Developer ID Application:"
codesign -s "Developer ID Application: {0}" --force --options runtime  ./target/release/bundle/osx/RustDeskIkoiTeachers.app/Contents/MacOS/*
codesign -s "Developer ID Application: {0}" --force --options runtime  ./target/release/bundle/osx/RustDeskIkoiTeachers.app
'''.format(pa))
            os.system('create-dmg target/release/bundle/osx/RustDeskIkoiTeachers.app')
            os.rename('RustDeskIkoiTeachers %s.dmg' % version, 'rustdesk-%s.dmg' % version)
            if pa:
                os.system('''
#rcodesign sign --p12-file ~/.p12/rustdesk-developer-id.p12 --p12-password-file ~/.p12/.cert-pass --code-signature-flags runtime ./rustdesk-{1}.dmg
codesign -s "Developer ID Application: {0}" --force --options runtime ./rustdesk-{1}.dmg
# https://pyoxidizer.readthedocs.io/en/latest/apple_codesign_rcodesign.html
rcodesign notarize --api-issuer 69a6de7d-2907-47e3-e053-5b8c7c11a4d1 --api-key 9JBRHG3JHT --staple ./rustdesk-{1}.dmg
# verify:  spctl -a -t exec -v /Applications/RustDesk.app
'''.format(pa, version))
            else:
                print('Not signed')
        else:
            os.system('mv target/release/bundle/deb/rustdesk*.deb ./rustdesk.deb')
            os.system('dpkg-deb -R rustdesk.deb tmpdeb')
            os.system('mkdir -p tmpdeb/usr/share/rustdesk/files/systemd/')
            os.system(
                'cp rustdesk.service tmpdeb/usr/share/rustdesk/files/systemd/')
            os.system(
                'cp rustdesk.service.user tmpdeb/usr/share/rustdesk/files/systemd/')
            os.system('cp pynput_service.py tmpdeb/usr/share/rustdesk/files/')
            os.system('cp -a DEBIAN/* tmpdeb/DEBIAN/')
            os.system('strip tmpdeb/usr/bin/rustdesk')
            os.system('mkdir -p tmpdeb/usr/lib/rustdesk')
            os.system('cp libsciter-gtk.so tmpdeb/usr/lib/rustdesk/')
            md5_file('usr/share/rustdesk/files/systemd/rustdesk.service')
            md5_file('usr/share/rustdesk/files/systemd/rustdesk.service.user')
            md5_file('usr/share/rustdesk/files/pynput_service.py')
            md5_file('usr/lib/rustdesk/libsciter-gtk.so')
            os.system('dpkg-deb -b tmpdeb rustdesk.deb; /bin/rm -rf tmpdeb/')
            os.rename('rustdesk.deb', 'rustdesk-%s.deb' % version)
    os.system("mv Cargo.toml.bk Cargo.toml")
    os.system("mv src/main.rs.bk src/main.rs")


def md5_file(fn):
    md5 = hashlib.md5(open('tmpdeb/' + fn, 'rb').read()).hexdigest()
    os.system('echo "%s %s" >> tmpdeb/DEBIAN/md5sums' % (md5, fn))


if __name__ == "__main__":
    main()

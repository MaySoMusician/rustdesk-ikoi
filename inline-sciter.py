#!/usr/bin/env python3

import re


def strip(s): return re.sub(r'\s+\n', '\n', re.sub(r'\n\s+', '\n', s))

def openUft8(path): return open(path, 'r', encoding='utf-8')

common_css = openUft8('src/ui/common.css').read()
common_tis = openUft8('src/ui/common.tis').read()

index = openUft8('src/ui/index.html').read() \
    .replace('@import url(index.css);', openUft8('src/ui/index.css').read()) \
    .replace('include "index.tis";', openUft8('src/ui/index.tis').read()) \
    .replace('include "msgbox.tis";', openUft8('src/ui/msgbox.tis').read()) \
    .replace('include "ab.tis";', openUft8('src/ui/ab.tis').read())

remote = openUft8('src/ui/remote.html').read() \
    .replace('@import url(remote.css);', openUft8('src/ui/remote.css').read()) \
    .replace('@import url(header.css);', openUft8('src/ui/header.css').read()) \
    .replace('@import url(file_transfer.css);', openUft8('src/ui/file_transfer.css').read()) \
    .replace('include "remote.tis";', openUft8('src/ui/remote.tis').read()) \
    .replace('include "msgbox.tis";', openUft8('src/ui/msgbox.tis').read()) \
    .replace('include "grid.tis";', openUft8('src/ui/grid.tis').read()) \
    .replace('include "header.tis";', openUft8('src/ui/header.tis').read()) \
    .replace('include "file_transfer.tis";', openUft8('src/ui/file_transfer.tis').read()) \
    .replace('include "port_forward.tis";', openUft8('src/ui/port_forward.tis').read())

chatbox = openUft8('src/ui/chatbox.html').read()
install = openUft8('src/ui/install.html').read().replace('include "install.tis";', openUft8('src/ui/install.tis').read())

cm = openUft8('src/ui/cm.html').read() \
    .replace('@import url(cm.css);', openUft8('src/ui/cm.css').read()) \
    .replace('include "cm.tis";', openUft8('src/ui/cm.tis').read())


def compress(s):
    s = s.replace("\r\n", "\n")
    x = bytes(s, encoding='utf-8')
    return '&[u8; ' + str(len(x)) + '] = b"' + str(x)[2:-1].replace(r"\'", "'").replace(r'"',
                                                                                  r'\"') + '"'


with open('src/ui/inline.rs', 'wt', encoding='utf-8') as fh:
    fh.write('const _COMMON_CSS: ' + compress(strip(common_css)) + ';\n')
    fh.write('const _COMMON_TIS: ' + compress(strip(common_tis)) + ';\n')
    fh.write('const _INDEX: ' + compress(strip(index)) + ';\n')
    fh.write('const _REMOTE: ' + compress(strip(remote)) + ';\n')
    fh.write('const _CHATBOX: ' + compress(strip(chatbox)) + ';\n')
    fh.write('const _INSTALL: ' + compress(strip(install)) + ';\n')
    fh.write('const _CONNECTION_MANAGER: ' + compress(strip(cm)) + ';\n')
    fh.write('''
fn get(data: &[u8]) -> String {
    String::from_utf8_lossy(data).to_string()
}
fn replace(data: &[u8]) -> String {
    let css = get(&_COMMON_CSS[..]);
    let res = get(data).replace("@import url(common.css);", &css);
    let tis = get(&_COMMON_TIS[..]);
    res.replace("include \\\"common.tis\\\";", &tis)
}
#[inline]
pub fn get_index() -> String {
    replace(&_INDEX[..])
}
#[inline]
pub fn get_remote() -> String {
    replace(&_REMOTE[..])
}
#[inline]
pub fn get_install() -> String {
    replace(&_INSTALL[..])
}
#[inline]
pub fn get_chatbox() -> String {
    replace(&_CHATBOX[..])
}
#[inline]
pub fn get_cm() -> String {
    replace(&_CONNECTION_MANAGER[..])
}
''')

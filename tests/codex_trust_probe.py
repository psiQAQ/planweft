"""Exercise Codex 0.149.1's native hooks review UI in an owned isolated HOME.

No trust file is synthesized. The caller installs and verifies the exact plugin
before invoking this function, and must subsequently check a fresh model session.
"""
import fcntl
import json
import os
from pathlib import Path
import pty
import re
import select
import signal
import struct
import subprocess
import termios
import time


def plain(text):
    text=re.sub(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)','',text)
    text=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',text)
    return re.sub(r'\s+','',text)


def review_action(text,stage):
    value=plain(text)
    if stage=='start' and 'Doyoutrustthecontentsofthisdirectory?' in value and 'Pressentertocontinue' in value:
        return b'\r','directory-approved'
    if stage in {'start','directory-approved'} and 'Hooksneedreview' in value and 'Pressentertoconfirm' in value:
        return b'\r','review-opened'
    if stage in {'start','directory-approved','review-opened'} and 'Pressttotrustall' in value:
        return b't','hooks-approved'
    if stage=='hooks-approved' and 'Pressentertoviewhooks' in value and 'Active' in value:
        return None,'verified-active'
    return None,stage


def stop_ui(process,master):
    if process is None or process.poll() is not None: return
    try: os.write(master,b'\x1b\x03\x03')
    except OSError: pass  # The slave may have closed between poll and write.
    for sig in [None,signal.SIGTERM,signal.SIGKILL]:
        if sig is not None:
            try: os.killpg(process.pid,sig)
            except ProcessLookupError: pass
        try: process.wait(timeout=5);return
        except subprocess.TimeoutExpired: continue
    raise RuntimeError('Owned native trust UI process did not exit')


def save_trace(output,chunks,actions,stage,sanitize):
    Path(output).write_text(sanitize(''.join(chunks)))
    Path(output).with_suffix('.actions.json').write_text(sanitize(json.dumps({'stage':stage,'actions':actions},indent=2)+'\n'))


def trust_hooks(model,work,output,timeout=90,*,sanitize):
    master,slave=pty.openpty()
    fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',40,120,0,0))
    command=['codex','--no-alt-screen','--disable','memories','--disable','multi_agent',
             '--model',model,'--cd',str(work)]
    env={**os.environ,'TERM':'xterm-256color'}
    process=None;chunks=[];window='';stage='start';actions=[];pending=None
    started=time.monotonic()
    def terminal_session():
        os.setsid()
        # A PTY fd alone is insufficient for crossterm's /dev/tty event input.
        # This owned child needs the slave as its controlling terminal.
        fcntl.ioctl(0,termios.TIOCSCTTY,0)
    try:
        process=subprocess.Popen(command,cwd=work,stdin=slave,stdout=slave,stderr=slave,
                                 env=env,preexec_fn=terminal_session)
        os.close(slave);slave=None
        while time.monotonic()-started<timeout:
            if process.poll() is not None: raise RuntimeError('Native trust UI exited before confirmation')
            ready,_,_=select.select([master],[],[],0.1)
            if ready:
                raw=os.read(master,65536);text=raw.decode(errors='replace')
                chunks.append(text);window+=text
                if '\x1b[6n' in text: os.write(master,b'\x1b[1;1R')
            action,next_stage=review_action(window,stage)
            if next_stage!=stage:
                if pending is None: pending=time.monotonic()
                # Startup renders can precede registration of native input
                # handlers. React once to a complete, settled observed prompt.
                if time.monotonic()-pending<1: continue
                actions.append({'from':stage,'to':next_stage,'seconds':round(time.monotonic()-started,3)})
                stage=next_stage;window='';pending=None
                if action: os.write(master,action)
            if stage=='verified-active': break
        if stage!='verified-active': raise RuntimeError('Native trust UI did not confirm active hooks before timeout')
        return {'status':'Passed','mechanism':'native TUI review then trust all owned plugin hooks',
                'argv':command,'actions':actions,'trust_file_synthesized':False}
    finally:
        # This process group was created here; never match unrelated processes.
        try:
            stop_ui(process,master)
        finally:
            try: save_trace(output,chunks,actions,stage,sanitize)
            finally:
                os.close(master)
                if slave is not None: os.close(slave)

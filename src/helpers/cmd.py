import os
import subprocess
import time
import re
import src.helpers.fo as fo
from src.helpers.logging import log


# exec bash cmd inside python:
#   cmd:          комманда
#   strict:       если команда завершилась ошибкой прекратить выполнение python скрипта
#   verbose4fail: выводить команду/return_code/stdout/stderr если была ошибка
#   verbose4ok:   выводить команду/return_code/stdout/stderr если ошибки небыло
#   verbose:      выводить команду/return_code/stdout/stderr ???
def cmd(cmd, strict=True, verbose4fail=True, verbose4ok=False, verbose=False):
    # validate params
    cmd = cmd.strip()
    if cmd == 'pwd':
        return {'code': 0, 'success': True, 'out': os.getcwd(), 'err': False}
    if cmd.split(' ', 1)[0] == 'cd':
        return os.chdir(cmd.split(' ', 1)[1])
    # run cmd
    reply = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, encoding='utf-8')
    # post-processing
    out = reply.stdout.strip()
    err = reply.stderr.strip()
    if reply.returncode == 0:
        success = True
        if verbose or verbose4ok:
            verbose_print(success, cmd, reply.returncode, err, out)
    if reply.returncode != 0 or err:
        success = False
        if verbose or verbose4fail:
            verbose_print(success, cmd, reply.returncode, err, out)
        if strict:
            exit()
    return {'code': reply.returncode, 'success': success, 'out': out, 'err': err}

def verbose_print(success, cmd, code, err, out):
    status = 'ok' if success else 'error'
    log('Run cmd', cmd, status)
    log('Return cmd [code]', '   '+str(code), status)
    log('Return cmd [std_err]', err, status)
    log('Return cmd [std_out]', out, status)

# def ssh(user, host, cmd, strict=True):
#     ssh_args=f'-o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout={co["global"]["ssh"]["timeout"]}'
#     result = run(f'ssh {user}@{host} {ssh_args} {cmd}', strict=strict)
#     if result['code'] == 0:
#         log('success', f'{user}@{host}: {cmd}')
#     else:
#         log('failed', f'{user}@{host}: {cmd}', 3)
#     return result

def check_ssh(host, user):
    if ssh(user, host, cmd='echo ok', strict=False)['code'] != 0:
        log('failed', host, 3)
        return False
    return True

def check_sudo(host, user):
    if ssh(user, host, cmd='sudo echo ok', strict=False)['code'] != 0:
        log('failed', host, 3)
        return False
    return True

def scp(src, dst, send_pass=False):
    print(dst.split(':', 1))
    host, f = dst.split(':', 1)
    print(host)
    print(f)
    exit()
    # TODO: check if is dir
    arg_r = '-r' if is_dir else ''
    pfx = f'sshpass -p {ssh_pass}' if send_pass else ''
    ssh_pfx = f'{pfx} ssh {ssh_user}@{dst}'
    scp_pfx = f'{pfx} scp {arg_r} {ssh_user}@{dst}'
    before_script = 'src/collector/nginx/scp_before.sh'
    commands = [
        f"if [ -d {target_dir} ]; then rm -r {target_dir}; fi",
        f"if [ -f {target_dir} ]; then rm {target_dir}; fi",
        f"mkdir -p {target_dir}",
        f"{ssh_pfx} 'bash -s' < {before_script} {ssh_user} {source_dir}",
        f"{scp_pfx}:/home/{ssh_user}/wofr_tmp {target_dir}",
        f"{ssh_pfx} 'rm -r /home/{ssh_user}/wofr_tmp'"
    ]
    for cmd in commands:
        self.run(cmd, strict=True, verbose4fail=True)

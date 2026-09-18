"""Linux Landlock write boundary. Read/network/process access is NOT isolated."""
import ctypes
import os
import platform
from pathlib import Path

class BoundaryUnavailable(RuntimeError):pass


def restrict_writes(output_dir):
    """Irreversibly restrict this process and descendants to writes under output."""
    if platform.system()!='Linux' or platform.machine() not in ('x86_64','aarch64'):
        raise BoundaryUnavailable('unsupported syscall architecture')
    root=Path(output_dir)
    if root.is_symlink() or not root.is_dir():
        raise BoundaryUnavailable('output must be an existing real directory')
    libc=ctypes.CDLL(None,use_errno=True)
    libc.syscall.restype=ctypes.c_long
    def call(number,*args):
        result=libc.syscall(ctypes.c_long(number),*args)
        if result<0:
            error=ctypes.get_errno()
            raise BoundaryUnavailable(f'Landlock syscall {number}: {os.strerror(error)}')
        return result
    abi=call(444,ctypes.c_void_p(),ctypes.c_size_t(0),ctypes.c_uint(1))
    if abi<3:raise BoundaryUnavailable('Landlock ABI >=3 required for truncate protection')
    # Handle every filesystem mutation right through ABI 3. Read/execute unchanged.
    mask=sum(1<<bit for bit in (1,4,5,6,7,8,9,10,11,12,13,14))
    class Ruleset(ctypes.Structure):_fields_=[('handled_access_fs',ctypes.c_uint64)]
    class PathBeneath(ctypes.Structure):
        _pack_=1
        _fields_=[('allowed_access',ctypes.c_uint64),('parent_fd',ctypes.c_int32)]
    spec=Ruleset(mask);ruleset=call(444,ctypes.byref(spec),ctypes.c_size_t(ctypes.sizeof(spec)),ctypes.c_uint(0))
    directory=os.open(root,os.O_PATH|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        rule=PathBeneath(mask,directory)
        call(445,ctypes.c_int(ruleset),ctypes.c_int(1),ctypes.byref(rule),ctypes.c_uint(0))
        if libc.prctl(38,1,0,0,0)!=0:raise BoundaryUnavailable('PR_SET_NO_NEW_PRIVS failed')
        call(446,ctypes.c_int(ruleset),ctypes.c_uint(0))
    finally:os.close(directory);os.close(ruleset)
    return {'mechanism':'linux_landlock','abi':abi,'write_root':str(root.resolve()),
            'read_isolation':'not_provided','network_isolation':'not_provided',
            'process_isolation':'not_provided','metadata_isolation':'not_provided'}


def main(argv=None):
    import argparse
    import sys
    import json
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args(argv)
    command=args.command[1:] if args.command[:1]==['--'] else args.command
    if not command:parser.error('a child command is required')
    try:boundary=restrict_writes(args.output)
    except Exception as exc:
        print(json.dumps({'status':'blocked','reason':str(exc)}),file=sys.stderr);return 4
    print(json.dumps({'status':'write_boundary_enabled','boundary':boundary}),file=sys.stderr,flush=True)
    os.execvp(command[0],command)

if __name__=='__main__':
    import sys
    sys.exit(main())

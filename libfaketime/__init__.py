import os
import sys

from contextdecorator import ContextDecorator
import dateutil.parser


def _get_shared_lib(basename):
    return os.path.join(
        os.path.dirname(__file__),
        os.path.join('..', 'vendor', 'libfaketime', 'src'),
        basename)

_platform_additions = {
    # keys are the first 5 chars since we don't care about the version.
    'linux': {
        'LD_PRELOAD': _get_shared_lib('libfaketime.so.1')
    },
    'darwi': {
        'DYLD_INSERT_LIBRARIES': _get_shared_lib('libfaketime.1.dylib'),
        'DYLD_FORCE_FLAT_NAMESPACE': '1',
    },
}


def _get_env_additions():
    try:
        env_additions = _platform_additions[sys.platform[:5]]
    except KeyError:
        raise RuntimeError("libfaketime does not support platform %s" % sys.platform)

    needs_reload = True
    if len(set(env_additions) & set(os.environ)) == len(env_additions):
        needs_reload = False

    return needs_reload, env_additions


needs_reload, env_additions = _get_env_additions()
if needs_reload:
    os.environ.update(env_additions)
    args = [sys.executable, [sys.executable] + sys.argv, os.environ]
    print 're-exec with libfaketime dependencies'
    os.execve(*args)

# All the environment variables have been used at this point.
# We remove them so that subprocesses don't get faked accidentally.
for key in env_additions:
    if key in os.environ:
        del os.environ[key]


class fake_time(ContextDecorator):
    def __init__(self, datetime_spec):
        _datetime = datetime_spec
        if isinstance(datetime_spec, basestring):
            _datetime = dateutil.parser.parse(datetime_spec)

        self.libfaketime_spec = _datetime.strftime('%Y-%m-%d %T %f')

    def __enter__(self):
        self.prev_spec = os.environ.get('FAKETIME')
        os.environ['FAKETIME'] = self.libfaketime_spec
        return self

    def __exit__(self, *exc):
        if self.prev_spec is not None:
            os.environ['FAKETIME'] = self.prev_spec
        else:
            del os.environ['FAKETIME']

        return False

    # Freezegun compatibility.
    start = __enter__
    stop = __exit__

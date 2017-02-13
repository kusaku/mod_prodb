from distutils.core import setup

import py2exe

print('py2exe v.{}'.format(py2exe.__version__))

setup(
    console=[
        {
            'script': 'prodb_mod_server.py',
            'icon_resources': [(0, 'icon.ico')]
        }
    ],
    version='0.1',
    url='http://www.aggrostudios.com/',
    license='Propietary',
    author='AggroStudios',
    author_email='kirill.a@aggrostudios.com',
    description='ProDB Mod server for WoT',
    options={
        'py2exe': {
            'unbuffered': False,
            'optimize': 0,
            'includes': [],
            'packages': [],
            'ignores': [],
            'excludes': [],
            'dll_excludes': [],
            'dist_dir': 'dist',
            'typelibs': [],
            'compressed': False,
            'xref': True,
            'bundle_files': 1,
            'skip_archive': False,
            'ascii': False,
            'custom_boot_script': ''
        }
    },
    # zipfile='library.zip',
    zipfile=None,
    data_files=[('', ['prodb_mod_server.cfg'])],
)

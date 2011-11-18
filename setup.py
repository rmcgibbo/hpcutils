from distutils.core import setup
import glob

setup(name='hpcutils',
      version = '1.0',
      description = 'HPC Utilities',
      author = 'rmcgibbo',
      author_email = 'rmcgibbo@gmail.com',
      url = '',
      packages = ['hpcutils'],
      package_data = {'hpcutils': ['config/*.yaml']},
      package_dir = {'hpcutils': 'lib'},
      scripts = glob.glob('scripts/*'),
      requires = ['pygments']
      )



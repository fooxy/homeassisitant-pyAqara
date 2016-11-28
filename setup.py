from setuptools import setup, find_packages

setup(name='pyAqara',
      version='0.1',
      description='Home-Assistant component for Aqara gateway integration',
      keywords='aqara gateway xiaomi lumi hub',
      author='fooxy',
      author_email='rabir.yadir@gmail.com',
      url='https://github.com/fooxy',
      zip_safe=False,
      platforms=["any"],
      packages=find_packages(),
      )
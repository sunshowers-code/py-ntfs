# -*- coding: utf-8 -*-
import os
import sys
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


version = '0.1.5'

long_description = (
    'Detailed Documentation\n'
    '**********************\n'
    + '\n' +
    read('README.rst')
    + '\n' +
    'Change history\n'
    '**************\n'
    + '\n' +
    read('CHANGES.txt')
    + '\n' +
    'Contributors\n'
    '************\n'
    + '\n' +
    read('CONTRIBUTORS.txt')
)
install_requires = ['setuptools']

extra = {}

setup(name='ntfsutils',
      version=version,
      description="A Python module to manipulate NTFS hard links and junctions.",
      long_description=long_description,
      classifiers=[
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
      ],
      keywords='windows ntfs hardlink junction',
      author='Rain',
      author_email='rain@sunshowers.io',
      url='https://github.com/sunshowers-code/py-ntfs',
      license='BSD',
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      **extra
      )

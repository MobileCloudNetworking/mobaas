from distutils.core import setup, Extension

module1 = Extension('flows_ts',
                    sources = ['flows_tsmodule.cc'])

setup (name = 'flows_ts',
       version = '1.0',
       description = 'This is the flows_ts module written in C.',
       ext_modules = [module1])
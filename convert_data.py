"""Compatibility entry point for the dataset converter."""
import runpy

if __name__ == '__main__':
    runpy.run_module('scripts.convert_data', run_name='__main__')

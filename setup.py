from setuptools import setup, find_packages

setup(name='biigle_scripts',
      version='1.0',
      packages=find_packages(),
      entry_points={
            'console_scripts': [
                  'convert_laser_circle_to_point=convert_laser_circle_to_point:main',
                  'pull_patches=pull_patches:main'
            ]}
      )
from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name='biigle_scripts',
      version='1.0',
      packages=find_packages(),
      install_requires=requirements,
      entry_points={
            'console_scripts': [
                  'convert_laser_circle_to_point=convert_laser_circle_to_point:main',
                  'pull_patches=pull_patches:main',
                  'review_annotations=review_annotations:main',
                  'compute_image_quality=compute_image_quality:main'
            ]}
      )
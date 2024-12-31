from setuptools import setup, find_packages

setup(
    name='geneni',
    version='0.1.0',
    description='AI agent for biological data',
    author='Duy Nguyen',
    author_email='duynguy@stanford.edu',
    url='https://github.com/yudduy/geneni',
    packages=find_packages(),
    install_requires=[
        'google-search-results>=2.4.2',
        'openai>=0.27.0',
        'pydantic>=1.10.5',
        'requests>=2.28.2'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: Stanford University License'
    ],
)

from setuptools import setup, find_packages


# Read the README file for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='impc_api',
    version='1.0.4',
    description='A package to facilitate making API request to the IMPC Solr API',
    author='MPI2, Marina Kan, Diego Pava',
    url='https://github.com/mpi2/impc-data-api-workshop',
    packages=find_packages(include=["impc_api", "impc_api.*"]),
    include_package_data=True,
    install_requires=[
        'pandas>=2.2.0',
        'requests>=2.31.0',
        'tqdm>=4.66.4',
        'pydantic>=2.9'
    ],

    extras_require={
        'dev': [
            'pytest>=8.2.2',
        ],
    },
    long_description=long_description,
    long_description_content_type='text/markdown',
    # classifiers=[
    #     'Development Status :: 3 - Alpha',
    #     'Intended Audience :: IMPC data users',
    #     'License :: OSI Approved :: MIT License',
    #     'Programming Language :: Python :: 3.10',
    #     'Operating System :: MacOS',
    #     'Operating System :: Microsoft :: Windows'
    # ],
    python_requires='>=3.10'
)

from setuptools import setup, find_packages

setup(
    name='impc_api_helper',
    version='0.1.0',
    description='A package to facilitate making API request to the IMPC Solr API',
    author='MPI2, Marina Kan, Diego Pava',
    url='https://github.com/mpi2/impc-data-api-workshop',
    packages=find_packages(),
    install_requires=[
        'pandas>=2.2.0',
        'requests>=2.31.0',
        'tqdm>=4.66.4',
    ],

    extras_require={
        'dev': [
            'pytest>=8.2.2',
        ],
    },
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
from setuptools import setup


setup(
    name='ado',
    version='0.3',
    packages=['src'],
    url='',
    license='',
    author='Owen.Mather',
    description='Simple CLI to Work with Azure DevOps Work Items',
    install_requires=[
        'PyYAML==6.0',
        'tabulate==0.9.0',
        'requests==2.28.2',
        'wcwidth==0.2.5',
        'beautifulsoup4==4.10.0'
    ],
    entry_points={
        'console_scripts': ['ado=src.ado:ado'],
    },
    include_package_data=True,
)

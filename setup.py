import setuptools

with open("README.md", "r") as file:
    long_description = file.read()


setuptools.setup(
    name='guspy',
    version='0.12',
    author='Liew Cher Don',
    author_email='liewcherdon@gmail.com',
    description='Simple Python Wrapper for common GUS Objects',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://git.soma.salesforce.com/c-liew/guspy',
    packages=['guspy'],
    data_files=[('resources', ['resources/cli.json', 'resources/objects.json'])],
    classifiers=[
     "Programming Language :: Python :: 3.7",
     "License :: OSI Approved :: MIT License",
     "Operating System :: OS Independent",
    ]
)
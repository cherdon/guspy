import setuptools

with open("README.md", "r") as file:
    long_description = file.read()


setuptools.setup(
    name='guspy',
    version='2.13',
    author='Liew Cher Don',
    author_email='liewcherdon@gmail.com',
    description='Simple Python Wrapper for common GUS Objects',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/cherdon/guspy',
    packages=['guspy'],
    data_files=[('resources', ['resources/cli.json', 'resources/objects.json'])],
    classifiers=[
     "Programming Language :: Python :: 3.8",
     "License :: OSI Approved :: MIT License",
     "Operating System :: OS Independent",
    ]
)
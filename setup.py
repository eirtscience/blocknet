import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="blocknet",  # Replace with your own username
    version="0.0.1",
    author="Fangnikoue Evarist",
    author_email="malevae@gmail.com",
    description="A script to Bring up a Hyperledger Fabric network with your own org setting.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eirtscience/blocknet",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)

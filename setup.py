import setuptools


setuptools.setup(
    name="blocknet",  # Replace with your own username
    version="0.0.2",
    author="Fangnikoue Evarist",
    author_email="malevae@gmail.com",
    description="Running private blockchain application using Hyperledger Fabric network, it is a pain when it comes to the configuration. Missing some configuration will deny the network to run. The pain of modifying the Hyperledger Fabric organization default setting. The lock into the Hyperledger fabric default two `orgs` and so on. If you are among those people, then welcome to `Blocknet`. A python package that is design to solve the above issues. `blocknet` allow you to generate the Hyperledger Fabric setting with only the provided configuration.",
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

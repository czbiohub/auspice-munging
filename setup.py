import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="auspicemunging", # Replace with your own username
    version="0.0.1",
    author="Joshua Batson",
    long_description=long_description,
    url="https://github.com/czbiohub/auspice-munging.git",
    packages=setuptools.find_packages(),
)

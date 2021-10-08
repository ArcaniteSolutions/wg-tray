import pathlib


from setuptools import find_packages, setup


# Get the long description from the README file
here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text()

# Get the global variables of the package
gv = {}
exec((here / "wgtray/__init__.py").read_text(), gv)

setup(
    name="wg-tray",
    version=gv["__version__"],
    description="A simple graphical tool to manage wireguard interfaces from the system tray",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Elsa Weber",
    author_email="elsa.weber@arcanite.ch",
    url="https://git.arcanite.ch/arcanite/wg-tray/",
    license="LICENSE.txt",
    packages=find_packages(),
    install_requires=[
        "pyqt5",
    ],
    package_data={"wgtray": ["res/*"]},
    scripts=["bin/wg-tray"],
)

from setuptools import setup

setup(
    name="muninn-sentinel5p",
    version="2.1",
    description="Muninn extension for official L1/L2/AUX Copernicus Sentinel-5P products",
    url="https://github.com/stcorp/muninn-sentinel5p",
    author="S[&]T",
    license="BSD",
    py_modules=["muninn_sentinel5p"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Environment :: Plugins",
    ],
    install_requires=["muninn"],
)

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="batchmark",
    version="0.1.0",
    description="CLI tool to benchmark batches of shell commands and output structured timing reports",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="batchmark contributors",
    python_requires=">=3.8",
    packages=find_packages(exclude=["tests*", "examples*"]),
    install_requires=[
        "pyyaml>=6.0",
        "tabulate>=0.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "batchmark=batchmark.cli:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Benchmark",
        "Environment :: Console",
    ],
)

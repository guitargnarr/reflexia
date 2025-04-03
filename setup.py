#!/usr/bin/env python3
"""
setup.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.
"""
Setup script for Reflexia Model Manager
"""

from setuptools import setup, find_packages
import os

# Read the requirements file
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Read the README file
with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name="reflexia-model-manager",
    version="1.0.0",
    author="Matthew Scott",
    author_email="matthewdscott7@gmail.com",
    description="A system for deploying, managing, and optimizing large language models with adaptive resource management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/guitargnar/reflexia-model-manager",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "reflexia=main:main",
        ],
    },
)
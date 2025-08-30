#!/usr/bin/env python3
"""Setup configuration for py-autotask."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [
            line.strip() for line in fh if line.strip() and not line.startswith("#")
        ]
except FileNotFoundError:
    # Fallback if requirements.txt is not found (e.g., in CI)
    requirements = [
        "requests>=2.31.0",
        "pydantic>=2.0.0",
        "click>=8.0.0",
        "python-dotenv>=1.0.0",
        "tenacity>=8.0.0",
        "httpx>=0.24.0",
        "typing-extensions>=4.0.0",
        "aiohttp>=3.8.0",
        "redis>=4.5.0",
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
        "pyarrow>=12.0.0",
        "tqdm>=4.65.0",
        "rich>=10.0.0",
    ]

setup(
    name="py-autotask",
    # Version is handled by setuptools_scm via pyproject.toml
    author="Aaron Sachs",
    author_email="asachs@wyre.engineering",
    description="A comprehensive Python client library for the Autotask REST API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/asachs01/py-autotask",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "responses>=0.23.0",
            "pytest-benchmark>=3.4.1",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "responses>=0.23.0",
            "pytest-benchmark>=3.4.1",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "bandit>=1.7.0",
            "safety>=2.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "py-autotask=py_autotask.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

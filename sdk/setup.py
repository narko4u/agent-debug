from setuptools import setup, find_packages

setup(
    name="agent-debug",
    version="0.1.0",
    description="Agent Execution Inspector & Replay SDK",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="AgentDebug",
    author_email="hello@agentdebug.dev",
    url="https://agentdebug.dev",
    license="MIT",
    packages=find_packages(),
    package_data={"agent_debug": ["py.typed"]},
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    install_requires=[],
    extras_require={
        "dev": ["pytest>=7.0", "pytest-cov>=4.0", "black>=23.0", "ruff>=0.1.0"],
    },
)

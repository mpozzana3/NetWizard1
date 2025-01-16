from setuptools import setup, find_packages

setup(
    name="cli_project",                # Nome del progetto
    version="1.0.0",                   # Versione del progetto
    author="Matteo Pozz",              # Tuo nome
    author_email="tuo_email@example.com",
    description="Un CLI che comunica con un server remoto.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/tuo-username/cli_project",  # URL del repository
    packages=find_packages(),          # Trova automaticamente i pacchetti (es. cli/, server/, shared/)
    install_requires=[
        "Flask>=2.3.2",
        "requests>=2.31.0",
        "pytest>=7.4.2"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "cli=cli.cli:main",       # Crea un comando CLI chiamato `cli`
        ],
    },
    python_requires=">=3.8",           # Versione minima di Python
)

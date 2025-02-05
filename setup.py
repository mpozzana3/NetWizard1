from setuptools import setup, find_packages

setup(
    name="NetWizard1",              
    version="1.0.0",                   
    author="Matteo Pozz",          
    author_email="tuo_email@example.com",
    description="Un CLI che comunica con un server sonda remoto e un server centrale. La CLI fa partire una scansione di sicurezza sulla rete del server remoto il quale salverà i dati sul suo DB e li invierà anche al DB centrale",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url=https://github.com/mpozzana3/NetWizard1.git,  # URL del repository
    packages=find_packages(),         
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

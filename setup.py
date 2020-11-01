from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

with open('VERSION') as f:
    version = f.read().strip()

setup(
    name='PhraseologyExtractionPackage',
    version=version,
    description='Package usable in command lines to extract phraseological patterns',
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Laurane Castiaux",
    author_email="laurane.castiaux@student.uclouvain.be",
    url="https://github.com/Reyla98/PhraseologyExtractionPackage",
    license=license,
    packages=find_packages(),
    py_modules=["lib/Ngram",
                "lib/Pattern"],
    data_files=[('config/PhraseologyExtractionPackage', ['config/default.json', 'config/Penn-Tree-Bank_simplified_tagset.json'])],
    entry_points={"console_scripts" : [
                    'PEP = PhraseologyExtractionPackage.__main__:main'
                    ]
                  },
    install_requires=["luigi"]
)
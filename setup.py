from babel.messages import frontend as babel
import setuptools

def read_requirements(filename):
    with open(filename, 'r') as file:
        return [line for line in file.readlines() if not line.startswith('-')]
setuptools.setup(
    name="legendarybot-bot",
    version="0.0.1",
    author="Greatman",
    author_email="notyourbusiness@test.com",
    description="LegendaryBot Bot",
    long_description="LegendaryBot Bot",
    long_description_content_type="text/markdown",
    url="https://github.com/LegendaryBot/bot",
    packages=setuptools.find_packages(),
    install_requires=read_requirements('requirements.txt'),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    cmdclass = {'compile_catalog': babel.compile_catalog,
                'extract_messages': babel.extract_messages,
                'init_catalog': babel.init_catalog,
                'update_catalog': babel.update_catalog},

)
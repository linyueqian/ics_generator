from setuptools import setup, find_packages

setup(
    name="ics_generator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.12.0",
        "icalendar>=5.0.11",
        "python-dotenv>=1.0.1",
        "pytz>=2024.1",
        "click>=8.1.7",
    ],
    entry_points={
        'console_scripts': [
            'ics-generator=ics_generator.cli:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A command-line tool to generate ICS calendar files using natural language",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ics_generator",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 
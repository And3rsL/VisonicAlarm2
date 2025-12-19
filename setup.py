import setuptools

setuptools.setup(
    name="visonicalarm2",
    version="3.3.6",
    author="Andrea Liosi",
    author_email="andrea.liosi@gmail.com",
    description="A simple API library for the Visonic/Bentel/Tyco Alarm system.",
    url="https://github.com/And3rsL/VisonicAlarm2",
    packages=setuptools.find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "python-dateutil>=2.8.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

from setuptools import setup, find_packages

setup(
    name='BatchMediaProcessingTools',
    version="0.1",
    url='https://github.com/akpw/batch-mp-tools',
    author='Arseniy Kuznetsov',
    author_email='k.arseniy@gmail.com',
    description=('CLI tools for batch media processing'),
    license='Apache License, Version 2.0',
    packages=find_packages(),
    keywords = "batch processing media video audio CLI ",
    scripts=['scripts/denoiser.py'],
    entry_points={'console_scripts': [
        'denoiser = scripts.denoiser:main',
    ]},
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Multimedia :: Sound/Audio :: Conversion",
        "Topic :: Multimedia :: Sound/Audio :: Noise reduction",
        "Topic :: Software Development :: Libraries",
        'Topic :: Utilities',
    ]
)




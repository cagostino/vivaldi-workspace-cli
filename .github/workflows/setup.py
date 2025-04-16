# setup.py
import setuptools
import os

# Function to read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print("Warning: README.md not found.")
        return "" # Return empty string if README is missing

setuptools.setup(
    name="vivaldi-workspace-cli",
    version="0.1.0",  # Initial version
    author="Your Name / Alias",
    author_email="your_email@example.com",
    description="CLI tool to launch Vivaldi and switch workspaces using keyboard shortcuts via PyAutoGUI.",
    long_description=read_readme(), # Read from README.md
    long_description_content_type="text/markdown", # Specify markdown format
    url="https://github.com/your_username/vivaldi-workspace-cli", # Optional: Link to repo
    license='MIT', # Or your chosen license identifier (e.g., 'GPL-3.0-only')
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8", # Specify versions supported
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License", # Match license choice
        "Operating System :: OS Independent", # Aspirational
        "Environment :: Console",
        "Topic :: Desktop Environment",
        "Topic :: Utilities",
    ],

    # --- Package Location ---
    package_dir={'': 'src'}, # Tell setuptools 'src' is the root for packages
    packages=setuptools.find_packages(where='src'), # Find packages under 'src'

    # --- Dependencies ---
    python_requires='>=3.8', # Minimum Python version
    install_requires=[
        'PyAutoGUI>=0.9.50', # Main dependency
        # Add any other direct dependencies here if needed later
    ],

    # --- Entry Point Script ---
    entry_points={
        'console_scripts': [
            'vivaldi_workspace = vivaldi_workspace_cli.cli:main', # command=package.module:function
        ],
    },
)
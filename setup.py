"""
Setup script for SafetyVision: VLM-Integrated Robotics for Nuclear Environments
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="safetyvision",
    version="0.1.0",
    author="Tirth Kanani",
    author_email="tirthkanani18@gmail.com",
    description="VLM-Integrated Robotics for Nuclear Safety Applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tirth8205/SafetyVision",
    project_urls={
        "Bug Tracker": "https://github.com/tirth8205/SafetyVision/issues",
        "Documentation": "https://github.com/tirth8205/SafetyVision/docs",
        "Source Code": "https://github.com/tirth8205/SafetyVision",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Manufacturing",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.3.0",
        ],
        "ros2": [
            "rclpy>=3.3.0",
            "geometry-msgs>=4.2.0",
            "sensor-msgs>=4.2.0",
            "nav-msgs>=4.2.0",
        ],
        "advanced": [
            "accelerate>=0.21.0",
            "bitsandbytes>=0.41.0",
            "xformers>=0.0.20",
        ],
    },
    entry_points={
        "console_scripts": [
            "safetyvision-dashboard=safetyvision.dashboard.monitoring_app:main",
            "safetyvision-analyze=safetyvision.cli.safety_cli:main",
            "safetyvision-robot=safetyvision.cli.robot_cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "safetyvision": [
            "config/*.yaml",
            "config/*.json",
            "assets/*",
            "docs/*",
        ],
    },
    keywords=[
        "artificial intelligence",
        "computer vision",
        "robotics",
        "nuclear safety",
        "vision language models",
        "safety monitoring",
        "autonomous systems",
        "multimodal AI",
    ],
)
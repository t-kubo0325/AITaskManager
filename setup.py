"""Setup configuration"""
from setuptools import setup, find_packages
from pathlib import Path

# README読み込み
readme = Path(__file__).parent / "README.md"
long_description = readme.read_text(encoding='utf-8') if readme.exists() else ""

setup(
    name='ai-task-manager',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'ai_task_manager': [
            'visualization/templates/*.html',
        ],
    },
    install_requires=[
        'click>=8.0.0',
        'jinja2>=3.0.0',
        'python-dateutil>=2.8.0',
    ],
    entry_points={
        'console_scripts': [
            'ai-task-manager=ai_task_manager.cli:cli',
        ],
    },
    author='Your Name',
    author_email='your.email@example.com',
    description='Claude Code対応タスク管理ツール',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/t-kubo0325/AITaskManager',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.8',
)

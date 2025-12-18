from setuptools import setup, find_packages

setup(
    name="reviewchain",
    version="1.0",
    py_modules=[
        "reviewchain",
        "reviewchain_main",
        "chat_env",
        "phase",
        "memory",
        "agents_local",
       
    ],
    packages=["prompts_template"],

    entry_points={
        "console_scripts": [
           "reviewchain = reviewchain:main",
        ]
    }
) 
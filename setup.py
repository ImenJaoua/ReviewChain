from setuptools import setup, find_packages

setup(
    name="cmtcheck",
    version="1.0",
    py_modules=[
        "cmtcheck",
        "cmtcheck_main",
        "chat_env",
        "phase",
        "memory",
        "agents_local",
       
    ],
    packages=["prompts_template"],  # or Prompts based on your repo name

    entry_points={
        "console_scripts": [
           "cmtcheck = cmtcheck:main",
        ]
    }
) 

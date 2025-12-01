from setuptools import setup, find_packages

setup(
    name="cmtcheck",
    version="1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "cmtcheck = cmtcheck:main",
        ]
    },
    py_modules=["cmtcheck", "cmtcheck_main", "chat_env",
                 "phase", "memory", "agents_local","comment_prompt",
                 "ref_prompt", "comment_prompt_AUTOMAT", "comment_prompt_chain_zero",
                 "comment_prompt_chain_few", "comment_prompt_Meta"],
) 

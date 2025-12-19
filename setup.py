from setuptools import setup, find_packages

setup(
    name="reviewchain",
    version="2.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "reviewchain = reviewchain:main",
        ]
    },
    py_modules=["reviewchain", "reviewchain_main", "chat_env",
                 "phase", "memory", "agents_local","comment_prompt",
                 "ref_prompt", "comment_prompt_AUTOMAT", "comment_prompt_chain_zero",
                 "comment_prompt_chain_few", "comment_prompt_Meta"],
) 

# Review Chain

Review Chain is an open-source, AI-powered tool designed to streamline and automate the code review process.

This project is built on intelligent communication between multiple AI agents.
These agents are responsible for reviewing and, when necessary, refining submitted code changes before they are merged into a target GitHub repository.

Submitted code passes through a structured code-review pipeline.

In the first step, a GitHub hunk is generated based on the changes applied to the file.
This hunk then moves through the pipeline, where relevant review comments are generated, required improvements are automatically applied, and the code is validated. Once the system approves the changes, the final refined version can replace the existing code after developer confirmation.

Review Chain significantly reduces the time and effort required for code review and approval. What traditionally takes hours can be completed in seconds using a single command.

In general, all Python and Java developers can benefit from this tool regardless of their project stack. By using the provided command-line interface, developers can easily review, refine, and update their code before committing it to GitHub.

The main advantages of Review Chain over similar tools include:

- Free and open-source usage.

- Lightweight design, using small, task-specific LLMs with reasonable computational requirements.

- Customizable, allowing modification and adaptation for specific projects or workflows.

- Secure for personal projects, with no concerns about data leakage due to its open-source nature.

- Seamless Git integration, connecting to GitHub through system credentials without additional configuration steps.

## Command line tool

After cloning the repository, run the following command inside your virtual environment to install the package:

```bash
pip install .
```

Once the package is installed, you can run it using the following command:

```bash
cmtcheck --path "path/to/target/file" --branch "target-branch-name"
```

Attention: The target file must already exist in your Git repository.
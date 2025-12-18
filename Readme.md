# ReviewChain
## An End-to-End, Feedback-Driven LLM System for Automated Code Review

ReviewChain is a lightweight command-line tool that automates code review using large language models (LLMs). Unlike existing tools that perform review tasks in isolation, ReviewChain models code review as an iterative, multi-stage pipeline, enabling comments, refinements, and quality assessment to inform each other through explicit feedback.

ReviewChain is not a code generation assistant. Instead, it targets a largely underserved part of the development workflow: iterative code review of existing changes. It focuses on helping developers review, refine, and improve code after it is written, closely mirroring real-world human review practices.

## Why ReviewChain?

Code review is essential but time-consuming. Developers often spend significant effort writing review comments, revising code, and validating changes—especially for small or repetitive issues.

Target users: 

  - Software developers

  - Open-source contributors

  - Teams seeking faster, more consistent code reviews

  - Researchers exploring multi-agent LLM systems for software engineering


The main advantages of Review Chain over similar tools include:

- Free and open-source usage.

- Lightweight design, using small, task-specific LLMs with reasonable computational requirements.

- Customizable, allowing modification and adaptation for specific projects or workflows.

- Secure for personal projects, with no concerns about data leakage due to its open-source nature.

- Seamless Git integration, connecting to GitHub through system credentials without additional configuration steps.

## Key Features
### 🔁 Iterative Review Pipeline

ReviewChain decomposes code review into four structured stages:

  1. Review Comment Generation – identifies issues and suggestions

  2. Comment Format Validation – ensures comments are clear and actionable

  3. Code Refinement – applies feedback to improve the code

  4. Quality Estimation – decides whether further refinement is needed

These stages are connected through an explicit feedback loop, allowing the system to improve outputs across multiple rounds.

### 🧩 Modular LLM Components
Each stage is handled by a specialized LLM, making the system:

  - Easier to extend or replace components

  - More interpretable than monolithic approaches

  - Well-suited for experimentation and research

### 💻 Simple Command-Line Interface

ReviewChain runs locally and integrates seamlessly with Git repositories. A single command triggers the full review pipeline.



## Installation & Setup

After cloning the repository, run the following command inside your virtual environment to install the package:

```bash
pip install .
```

Once the package is installed, you can run it using the following command:

```bash
reviewchain --path "path/to/target/file" --branch "target-branch-name"
```

Attention: The target file must already exist in your Git repository.

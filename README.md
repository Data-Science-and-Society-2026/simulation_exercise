# Simulation Exercise

This exercise is about making an AI tutor that can help students while studying. The project consists of a few project groups:

- **Speech to Text & Text to Speech**  
  - Make sure the AI can understand the user and can talk back to the user.
- **AI - RAG**  
  - Make a model that can help the user with their questions while using documents.
- **VR - Avatar**  
  - Make a virtual avatar that can help the user with their questions and make it more interactive.
- **Integration and Git**  
  - Ensure all the tools work together and that the project is well documented.
- **DPIA and GDPR**  
  - Ensure the project is GDPR compliant and consider ethical issues.

<details>
  <summary><h2>Project Setup</h2></summary>

  <details>
    <summary><h3>Windows Setup</h3></summary>

  To run the complete project with the correct dependencies, you first need to install a package manager. Follow the instructions to install [Chocolatey](https://docs.chocolatey.org/en-us/choco/setup/).

  Then install `make`:

  ```bash
  choco install make
  ```

  Once installed you can simply run:

  ```bash
  make setup
  ```

  And then:

  ```bash

  make python_deps

  ```
  </details>


  <details><summary><h3>MacOs Setup</h3></summary>


  This will install for `MacOs` users [homebrew](https://brew.sh/) and [uv](https://docs.astral.sh/uv/).If you already have a package manager and `uv` already installed,to be able to have all of the required dependencies run:

  ```bash 
  make setup
  ```

  ```bash
  make python_deps
  ```
  or the same:

  ```bash
  uv sync
  ```
</details>
</details>


  If an enviroment existed already it will update the dependencies. If one did not exist, it will create it and populate it.
  Check [uv documentation](https://docs.astral.sh/uv/getting-started/features/) for more information

# Simulation Exercise

<details><summary><h2>Project Setup</h2></summary>

  To run the project locally you can first run:
  ```bash
  make setup
  ```
  This will install for `MacOs` users [homebrew](https://brew.sh/) and [uv](https://docs.astral.sh/uv/). If  you are a `Windows` user it will install [chocolatey](https://chocolatey.org/) and `uv`.
  If you already have a package manager and `uv` already installed,to be able to have all of the required dependencies run:

  ```bash
  make python_deps
  ```
  or the same:

  ```bash
  uv sync
  ```
  If an enviroment existed already it will update the dependencies. If one did not exist, it will create it and populate it.
  Check [uv documentation](https://docs.astral.sh/uv/getting-started/features/) for more information
</details>

# Simulation Exercise

## Getting started
To get started with the project you first have to clone the repository into your local machine.Of course to be able to do so you need top install git in your machine. If on mac, you already have it installed, on windows have a look at https://git-scm.com/downloads. After that, to have the code in your local machine you can run:

```bash
git clone git@github.com:Data-Science-and-Society-2026/simulation_exercise.git
git clone https://github.com/Data-Science-and-Society-2026/simulation_exercise.git
```

<details>
  <summary><h2>Project Setup</h2></summary>

  To be able to have all of the required dependenciees run:
  ```bash
  make python_deps
  ```
  It requires [uv](https://docs.astral.sh/uv/). If you dont have a package manager you can also run :
  ```bash
  make setup
  ```
  This will install for `MacOs` users [hommebrew](https://brew.sh/) and `uv`. If `Windows` user it will intall [chocolatey](https://chocolatey.org/) and `uv`


  Once installed, to have get the python dependencies you can run:
  ```bash
  uv sync
  ```
  Check [uv documentation](https://docs.astral.sh/uv/getting-started/features/) for more information


</details>

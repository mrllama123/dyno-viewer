# dyn-cli

## dev notes

### prerequisites

needs python 3.10.7 and cpython library is installed. If you are using asdf to manage python then install python with this command

```bash
env PYTHON_CONFIGURE_OPTS="--enable-shared" asdf install python 3.10.7
```
or if using pyenv:

```bash
env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.10.7
```

see [how to build cpython with --enable-shared](https://github.com/pyenv/pyenv/wiki#how-to-build-cpython-with---enable-shared) for more info

### compile app

to compile the app go into the virtual env via command:
```bash
poetry shell
```
and then run:
```bash
pyinstaller  dyn_cli/app.py -F
```

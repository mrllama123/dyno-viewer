# dyna-cli

This is a experimental project i created out of frustration of how crap the dynamodb console is and from what i found there was no good app out there that had what i wanted.
Which basically boils down to a few things:

- display the table data in a simple spreadsheet form i.e something similar to an excel spreadsheet
- have keyboard shortcuts for traversing the data and app
- make it easy to switch between different aws accounts and regions
- the ui is simple and fast
- easy to run in cli

This also gave me a good excuse to try out the [textual](https://github.com/textualize/textual/) cli app framework :slightly-smiling-face:. I give no guaranties on the 
code quality as this came out of a friday hack session and i'm still getting to grips with the textual library. So there is probably better ways of doing what i have done

## dev notes

### prerequisites

this repo uses [poetry](https://python-poetry.org/docs/) for package management and needs python 3.10.7 installed either via [pyenv](https://github.com/pyenv/pyenv)
or [asdf](https://asdf-vm.com/) using the [asdf-community/asdf-python](https://github.com/asdf-community/asdf-python) addon 

For compiling the app locally you also need to ensure that cpython library is installed, With python env setup. 
If you are using asdf install python with this command:

```bash
env PYTHON_CONFIGURE_OPTS="--enable-shared" asdf install python 3.10.7
```
or if using pyenv:

```bash
env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.10.7
```

see [how to build cpython with --enable-shared](https://github.com/pyenv/pyenv/wiki#how-to-build-cpython-with---enable-shared) for more info

### local dev setup

to install locally run:
```bash
poetry install
# to go into a virtual env shell 
poetry shell
# or run app via script
poetry run run_app
```


### compile app locally

to compile the app go into the virtual env via command:
```bash
poetry shell
```
and then run pyinstaller:
```bash
pyinstaller  dyn_cli/app.py -F
```

then in the `dist\app` folder there will be the binary file



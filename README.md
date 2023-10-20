![screenshot](dyno-viewer-screenshot.png)
# Dyno-viewer

Dyno-viewer is dynamodb table viewer for your terminal build using [textual](https://github.com/Textualize/textual). 

This came out from me being frustrated with how clunky and slow the dynamodb viewier is in the aws console and me finding no good free alternative, That works the way i want it to work. 
Which is basically a spreadsheet with menus to change the table etc just like the aws console version and it being able to be used with just a keyboard


**Note:**

This is still in early alpha so some things to be expect things to be broken, I will fix them as i have time. Prs are welcome 

## Installing

### prerequisites

You need the [aws cli](https://aws.amazon.com/cli/) fully configured (see [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-authentication.html) for how to setup up auth) 

#### note about AWS IAM Identity Center(used to be called aws sso) aws profiles:

if you are using sso profiles. Then you need to make sure that you have updated your config to use a sso-session profile otherwise the app won't work see this [doc](https://docs.aws.amazon.com/cli/latest/userguide/sso-configure-profile-token.html) on how to do that. See this issue: https://github.com/boto/botocore/issues/2374 if you want to know why this is the case 

right now this can be installed via flatpak and pip:

### install

I recommend using [pipx](https://github.com/pypa/pipx):

```bash
pipx install dyno-viewer
```

## Dev notes

### Prerequisites

This repo uses [poetry](https://python-poetry.org/docs/) for package management and needs python 3.10+ installed either via [pyenv](https://github.com/pyenv/pyenv)
or [asdf](https://asdf-vm.com/) using the [asdf-community/asdf-python](https://github.com/asdf-community/asdf-python) addon

e.g:

```bash
env PYTHON_CONFIGURE_OPTS="--enable-shared" asdf install python 3.10.11
```
or if using pyenv:

```bash
env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.10.11
```

see [how to build cpython with --enable-shared](https://github.com/pyenv/pyenv/wiki#how-to-build-cpython-with---enable-shared) for more info

### Local dev setup

To install locally run:
```bash
poetry install
# to go into a virtual env shell 
poetry shell
# or run app via script
poetry run dyno-viewer
```

### Testing textual notes

See [testing notes doc](docs/testing-textual.md)


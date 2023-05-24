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

you also need the [aws cli](https://aws.amazon.com/cli/) fully configured (see [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-authentication.html) for how to setup up auth) 

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

#### note about AWS IAM Identity Center(used to be called aws sso) aws profiles

if you are using sso profiles. Then you need to make sure that you have updated your config to use a sso-session profile otherwise the app won't work see this [doc](https://docs.aws.amazon.com/cli/latest/userguide/sso-configure-profile-token.html) on how to do that. See this issue: https://github.com/boto/botocore/issues/2374 if you want to know why this is the case 

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
pyinstaller --add-data "dyna_cli/components/css:./components/css" dyna_cli
```

then in the `dist\app` folder there will be the binary file



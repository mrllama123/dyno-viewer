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


### flatpak notes

this repo supports flatpak building to make the process easy there is a script that builds the flatpak, Which are loosely created from this really useful [blog post](https://www.loganasherjones.com/2018/05/using-flatpak-with-python/). To run call:

```bash
poetry run flatpak_build
```

This will export the main packages into a requirements file and then build flatpak in the `.flatpak` folder then export that flatpak to a binary file in root called `dyna-cli.flatpak` which can be installed on another computer via `flatpak install dyna-cli.flatpak`

It also has support for doing other different options via arguments:

#### install locally

``` bash
poetry run flatpak_build -i 
```

This will install the flatpak locally instead of exporting it to a file (Useful for dev testing), Which then you can run it via:

```bash
flatpak run org.flatpak.dyna-cli
```

#### gpg key support

You can pass a gpg key for signing a flatpak, Which is best practice (see more on that [here](https://docs.flatpak.org/en/latest/flatpak-builder.html#signing)) via:

```bash
poetry run flatpak_build --gpg "<key id>"
```

If the gpg key is not in the default directory then you can also add the path to it via this argument:

```bash 
poetry run flatpak_build --gpg "<key id>" --gh path/to/gpg/key
```

**Master:**   
[![Build Status](https://travis-ci.com/threefoldtech/jumpscaleX.svg?branch=master)](https://travis-ci.com/threefoldtech/jumpscaleX)
[![codecov](https://codecov.io/gh/threefoldtech/jumpscaleX/branch/master/graph/badge.svg)](https://codecov.io/gh/threefoldtech/jumpscaleX)  
**Development:**  
[![Build Status](https://travis-ci.com/threefoldtech/jumpscaleX.svg?branch=development)](https://travis-ci.com/threefoldtech/jumpscaleX)
[![codecov](https://codecov.io/gh/threefoldtech/jumpscaleX/branch/development/graph/badge.svg)](https://codecov.io/gh/threefoldtech/jumpscaleX)


# Jumpscale

Jumpscale is a cloud automation product and a branch from what used to be 
Pylabs. About 9 years ago Pylabs was the basis of a cloud automation product 
which was acquired by SUN Microsystems from Q-Layer. In the mean time we are 
4 versions further and we have rebranded it to Jumpscale.

- [Jumpscale](#jumpscale)
  - [About Jumpscale](#about-jumpscale)
  - [Installing Jumpscale](#installing-jumpscale)
  - [Usage](#usage)
  - [Tutorials](#tutorials)
  - [Collaboration Conventions](#collaboration-conventions)

## About Jumpscale

Some tools available in jumpscale

* [Config Manager](docs/config/configmanager.md)
  The config manager is a secure way to manage configuration instances.
  Anything saved to the file system is NACL encrypted and only decrypted on
  the fly when accessed.

* [Executors](docs/Internals/Executors.md)
  Jumpscale comes with its own executors that abstract working locally or
  remotely.  Of these executors:

  * SSH Executor (for remote execution)
  * Local Executor (for local execution)
  * Docker Executor (for executing on dockers)

* [Builders](docs/Internals/Builders.md)
  Builder tools is a set of tools to perform the common tasks in your builder (e.g read a file , write to a file, execute bash commands and many other handy methods that you will probably need in your builder) \
  To create a builder see [documentation](docs/howto/Create\ a\ new\ Builder.md)

## Installing Jumpscale

[See documentation](/docs/Installation/install.md)


## Usage

* The jsshell
  in your terminal, type `js_shell`

* Kosmos in your terminal, type `kosmos`

* In Python

  ```bash
  python3 -c 'from Jumpscale import j;print(j.application.getMemoryUsage())'
  ```

  the default mem usage < 23 MB and lazy loading of the modules.

## Running Tests
To run unittests you can execute the following command
```bash
source /sandbox/env.sh; pytest /sandbox/code/github/threefoldtech/jumpscaleX/
```

You can also run Integration tests by running the command
```bash
source /sandbox/env.sh; pytest  --integration /sandbox/code/github/threefoldtech/jumpscaleX/
```

To annotate the one of your tests is an itegeration test rather than a unittests, you can add the following docorator to the test
```python
@pytest.mark.integration
def test_main(self)
```

## Tutorials

[Check Documentation](docs/howto/README.md)


## Collaboration Conventions
[check conventions](docs/CONTRIBUTING.md)

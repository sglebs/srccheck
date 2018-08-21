# Supported tags and respective `Dockerfile` links

-	[`und-5.0.955`, `latest`, (*Dockerfile*)](https://github.com/sglebs/srccheck/Dockerfile)

## How to use this image

* Using srccheck utilities:

```bash
docker run --rm -it -v "${PWD}:/project" -w "/project" sglebs/srccheck
```

* [SciTools Understand][] command lines utility can also be used directly:

```bash
docker run --rm -it -v "${PWD}:/project" -w "/project" sglebs/srccheck und help
```

* If your docker host provides a [X Window System][], [SciTools Understand][] can be executed in *GUI* mode. You'll need [display access][] to the user that's running the command:

```bash
docker run --rm -it -e DISPLAY="${DISPLAY}" -v "${PWD}:/project" -w "/project" -v "/tmp/.X11-unix:/tmp/.X11-unix" sglebs/understand understand
```

## Environment variables

Below a list of [environment variables](https://docs.docker.com/engine/reference/run/#env-environment-variables) that can be used to configure this image execution:

| Name | Description | Default value |
|---|---|---|
| UNDERSTAND_EVALCODE | Evaluation license code provided to run [SciTools Understand][] | - |
| UNDERSTAND_SDLCODE | Single developer license code provided to run [SciTools Understand][]. `USER_EMAIL_ACCOUNT` must be also provided to enable this activation method | - |
| UNDERSTAND_USER_EMAIL_ACCOUNT | User email account associated with `SDL` license used to activate [SciTools Understand][]. `SDLCODE` must be also provided to enable this activation method | - |
| UNDERSTAND_FLOATING_LICENSE_SERVER | Address used to connect [SciTools Understand][] client to a license server | - |
| UNDERSTAND_FLOATING_LICENSE_SERVER_PORT | Port used to connect [SciTools Understand][] client to a license server. `UNDERSTAND_FLOATING_LICENSE_SERVER` must be also provided to enable this activation method | 9000 |

## License

Since [SciTools Understand][] is bundled, it must be [activated][]. This image provides a few methods to achieve that (check the section above). If you have any doubts regarding [Scitools Understand][] licensing, please read their [end user license agreement][].

Also, since the first execution saves activation information in `~/.config/SciTools` (check the [Dockerfile](https://github.com/sglebs/srccheck/Dockerfile)), it's recommended to create a [docker volume][] to persist user data between executions. Below an example when using `FLOATING_LICENSE_SERVER` activation method:

* Creating the volume:

```bash
docker volume create und-data
```

* Running:

```bash
docker run --rm -it -e FLOATING_LICENSE_SERVER="license_server_host" -v "und-data:/root/.config/SciTools" -v "${PWD}:/project" -w "/project" sglebs/srccheck
```

[X Window System]: https://en.wikipedia.org/wiki/X_Window_System
[display access]: https://askubuntu.com/questions/654966/enable-x-display-access-for-local-user
[activated]: https://scitools.com/support/running-understand-headless-linux-server/
[end user license agreement]: https://scitools.com/eula/
[environment variables]: https://docs.docker.com/engine/reference/run/#env-environment-variables
[SciTools Understand]: https://scitools.com/features/
[docker volume]: https://docs.docker.com/engine/reference/commandline/volume_create/
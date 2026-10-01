# The docker daemon branch

Read this only when the user opts in to a docker daemon inside the sandbox.

Some test suites start containers. A **container-based test suite** needs a
docker daemon it can reach. This branch runs one inside the sandbox.

Every decision here comes from a fault that happened. Do not simplify one away.

## The cost

`runArgs` carries `--privileged`. It replaces `--cap-add=NET_ADMIN` and
`--cap-add=NET_RAW`, which the firewall needs and which privileged already
covers.

State this cost in the summary. The container gets the host kernel's full
surface, which is much more than the firewall alone needs. It still cannot reach
the host daemon, so it cannot start containers on the host and cannot mount the
host filesystem.

Never mount the host docker socket. That grants root on the host to anything in
the container, which is the one thing the sandbox prevents. Privileged is wider
inside the container and narrower on the host. Take the narrower host.

Rootless docker is blocked on a WSL2 kernel. Writing another process's `uid_map`
fails with `EIO`, as root and holding `CAP_SETUID`. Do not spend a build finding
this again.

Put the reason in a comment in `devcontainer.json`, so the next reader does not
undo it.

## The image

Install docker from the static archive. Do not use the distribution package: it
brings a service manager the container cannot run.

Extract these binaries: `docker`, `dockerd`, `containerd`,
`containerd-shim-runc-v2`, `runc`, `ctr`, `docker-proxy`, `docker-init`.

`docker-proxy` is not optional. Without it the daemon refuses to start with
`userland-proxy is enabled, but userland-proxy-path is not set`. A test suite
reaches a container through a published port, and a published port needs the
proxy.

Add `iproute2`, `iptables`, `ipset`, and `dnsutils` if the firewall has not
already added them.

Copy `start-docker` to `/usr/local/bin/start-docker` and make it executable.

Set `DOCKER_HOST` to `unix:///var/run/docker.sock`.

## Starting the daemon

The daemon does not start with the container. `start-docker` starts it. A session
that runs no integration test then pays nothing.

`start-docker` picks the storage driver by reading the filesystem type under
`/var/lib/docker`. An overlay filesystem cannot stack another overlay on itself,
so the daemon fails with `failed to mount overlay: invalid argument`. The script
takes the copying driver instead, which works anywhere and is slow and large.
`DOCKER_STORAGE_DRIVER` overrides the choice.

Do not check `/proc/filesystems` instead. It says overlay is available, not that
it can nest.

## The firewall and the daemon

Start the daemon after the firewall.

`init-firewall.sh` runs `iptables -F` and `iptables -X`. That deletes the
`DOCKER` chain the daemon creates at startup. Publishing a port then fails with
`No chain/target/match by that name`, which names nothing that points at the
firewall.

Re-running the firewall does it again. Restart the daemon after.

`sandbox-check` asserts the chain is present, so the check catches this.

## Pulling images

Images cannot be pulled through the firewall.

Add these hosts to the allowlist: `registry-1.docker.io`, `index.docker.io`,
`auth.docker.io`, and `production.cloudflare.docker.com`. They get the manifest
and the auth token.

They do not get the layers. Docker Hub serves blobs from a CDN on hostnames that
are not fixed, and the allowlist is an ipset of addresses resolved once. A layer
pull fails on an address nothing can predict.

So pull once with the firewall down:

```sh
sandbox-firewall-off
start-docker
docker pull <image>
sudo init-firewall.sh
```

After that the images are local and the tests run behind the firewall.

Write this workflow into the project's agent instructions file, if it has one.
The next session needs it and cannot work it out.

## What not to carry

Do not disable the test library's container reaper. That is one project's
judgment, not a rule.

Do not install the rootless extras. Nothing here uses them.

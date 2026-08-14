---
name: create-sandbox
description: Write a .devcontainer/ that runs Claude with permission checks off, behind a deny-by-default firewall. Use when the user wants a sandbox, a dev container for Claude, or to run Claude without permission prompts.
---

Write a dev container that runs Claude with permission checks off.

A **sandbox** is a container that limits what Claude reaches. Bypass mode is only
safe inside one. So this skill closes the network by default.

The container must work on the first open. Copy the scripts in `files/` rather
than writing your own. Each one carries fixes that cost a build to find.

Read the project. Ask only what you cannot work out. Show every decision. Wait.
Then write the files.

## Process

1. Discover. Read the project before you ask anything.
2. Interview. Ask only what discovery left open.
3. Summarise every decision and wait for the user's word.
4. Write the files.
5. Verify. Offer to build the container and run the check.
6. Report what you wrote. Stop.

## 1. Discover

Never ask what you can find out. Look for:

- `Dockerfile`, `docker-compose.yml`, and `compose.yaml` in the project root
- The last `USER` line of any Dockerfile you will use
- The package manager in the image: `apt-get`, `apk`, `dnf`, or none
- Whether the image carries `sudo`
- Package manifests: `package.json`, `pyproject.toml`, `requirements.txt`,
  `go.mod`, `Cargo.toml`, `Gemfile`, `composer.json`
- An existing `.devcontainer/`

Run these two commands as well:

- `id -u && id -g`, for the host uid and gid
- `find ~/.claude -maxdepth 1 -type l -exec readlink -f {} \;`, for the host
  paths that host symlinks point at

### The base image

Reuse a project image only when it is a **development image**. A development
image carries the language toolchain in its final stage. It expects the source
tree as its workspace.

Reject a project image when any of these is true:

- It is a multi-stage build whose final stage is a slim or distroless image.
- Its final stage copies built artefacts in and holds no compiler.
- Its `ENTRYPOINT` or `CMD` runs the application.

A production image is not a dev image. Reusing one gives a container with no
toolchain.

Reuse a compose file only when one of its services builds the project's own
source. Use the `dockerComposeFile` and `service` keys. A compose file of
databases, queues, and caches is not a dev host. The sandbox reaches those
services over the network. Ask nothing about them.

When no image qualifies, write a Dockerfile from the stack's official toolchain
image.

Never rewrite an image the project owns. Extend it instead. Add Claude, the
extension, and the firewall tooling through `postCreateCommand`, or through a
thin Dockerfile that builds `FROM` the project image.

### The user

Read the last `USER` line of the image you will use.

- No `USER` line, or `USER root`: the container runs as root.
- Any other value: the container runs as that user.

In a Dockerfile you write, create the user with the host's uid and gid. Write the
numbers literally.

A matching uid keeps the owner of every file in the bind-mounted workspace. It
also removes the recursive `chown` of the home directory. That `chown` would walk
the host's real `~/.claude`, which is mounted.

Keep a `chown` only when the uid cannot match.

### The docker signal

Look for a container-based test library in the manifests. `testcontainers` is
one. A test suite that starts containers is another.

When you find one, read `reference/docker-daemon.md` and ask. When you find
none, say nothing about docker.

## 2. Interview

Ask one question at a time. Wait for the answer.

Give your recommended answer with each question, so the user can reply "yes".

Ask only what changes the shape of the container. Default anything cheap to
change.

A single dev Dockerfile is a decision, not a question. A `USER` line is a
decision. A production image is a decision: reject it. A lone `package.json` is a
decision. Ask nothing in a project that answers itself.

Ask when:

- A container-based test library is present, so the docker daemon branch may
  apply.
- A compose file holds several services and more than one builds the source.
- The image has no package manager you recognise, so you cannot install the
  firewall tooling. Offer skipping the firewall as one answer.

## 3. Summarise and wait

Print a summary. List:

- The base image, and whether it comes from the project or is fresh
- The container user, the uid, and whether it is root
- The files you will write
- The network allowlist, with every host named
- The mounts, with every host path named
- The docker daemon branch, and its cost, when it applies

Write nothing until the user confirms.

If the user changes a decision, apply it, print the summary again, and wait
again. Repeat as often as the user needs.

If `.devcontainer/` already exists, name the files you would replace. Wait. Do
not merge with an existing `devcontainer.json`.

## 4. Write

Copy these files from this skill's `files/` directory into `.devcontainer/`:

- `init-firewall.sh`, unless the user skipped the firewall
- `sandbox-firewall-off`
- `sandbox-check`
- `start-docker`, only for the docker daemon branch

Copy them. Do not retype them. Then edit `init-firewall.sh` to fill its
allowlist, and delete the `TODO(create-sandbox)` comments you replace.

Write these files yourself:

- `.devcontainer/devcontainer.json`, always
- `.devcontainer/Dockerfile`, when no project image qualifies, or when a reused
  image needs `sudo`

Write no other file.

### devcontainer.json

Use this shape. Swap the image key for the one discovery chose.

```json
{
  "name": "<project> sandbox",
  "build": { "dockerfile": "Dockerfile", "context": "." },
  "workspaceFolder": "/workspace",
  "workspaceMount": "source=${localWorkspaceFolder},target=/workspace,type=bind",
  "runArgs": ["--cap-add=NET_ADMIN", "--cap-add=NET_RAW"],
  "remoteUser": "<user>",
  "remoteEnv": { "IS_SANDBOX": "1" },
  "mounts": [
    "source=${localEnv:HOME}/.claude,target=<home>/.claude,type=bind",
    "source=<host path>,target=<host path>,type=bind"
  ],
  "customizations": {
    "vscode": {
      "extensions": ["anthropic.claude-code"],
      "settings": {
        "claudeCode.allowDangerouslySkipPermissions": true,
        "claudeCode.initialPermissionMode": "bypassPermissions"
      }
    }
  },
  "postCreateCommand": "...",
  "postStartCommand": "sudo /usr/local/bin/init-firewall.sh"
}
```

### The mounts

Mount all of `~/.claude`, read-write. The target follows the container user. Root
gets `/root/.claude`. A named user gets that user's home directory.

The mount is read-write for two reasons. Claude refreshes its OAuth token and
writes the new one back. A read-only mount forces a login when the token
expires.

Then add one mount for every host symlink discovery found. A symlink under
`~/.claude` comes through the bind mount verbatim. It points at an absolute host
path, and that path does not exist in the container, so the link dangles. This is
what makes host skills vanish inside the container.

For each such path, add a bind mount whose source and target are that same path.
The link then resolves on both sides.

Skip a link whose target is inside `~/.claude`. The first mount already covers
it.

Do not rewrite the symlink. The host shares it.

Do not hardcode a path. Read the links at write time.

### Bypass mode in the extension

Set both settings keys. The first unlocks the mode. The second selects it for new
conversations. One without the other still prompts.

Add `anthropic.claude-code` to the extensions list, so it is there on first open.

### Bypass mode in the shell

Write a shell alias named `claude` that runs
`claude --dangerously-skip-permissions`.

Put it in the container user's shell profile from `postCreateCommand`. The
console and the extension then behave the same way.

### Root

Claude Code refuses bypass mode as root. The check is exact:

```
permissionMode === "bypassPermissions"
  && process.getuid() === 0
  && process.env.IS_SANDBOX !== "1"
  && process.env.CLAUDE_CODE_BUBBLEWRAP !== "1"
  -> print an error and exit
```

For a root container, set `IS_SANDBOX` to `"1"` in `remoteEnv`. For any other
user, leave the variable out.

Use `IS_SANDBOX`. Do not use `CLAUDE_CODE_BUBBLEWRAP`.

### postCreateCommand

It does three things:

1. Installs the Claude Code CLI from npm.
2. Installs the three scripts into `/usr/local/bin` with mode `0755`.
3. Appends the bypass alias to the container user's shell profile.

For a reused image, it also installs the firewall tooling with the image's
package manager. A Dockerfile you write installs it at build time instead.

The tooling is four packages, and all four are needed:

- `iptables`, for the rules
- `ipset`, for the address set
- `iproute2`, because the script reads the container subnet with `ip route`
- `dnsutils`, because the script resolves each host with `dig`

`iproute2` is the one that gets forgotten. The script then fails with
`ip: command not found`.

One `install` call takes every script:

```sh
sudo install -m 0755 .devcontainer/init-firewall.sh .devcontainer/sandbox-firewall-off .devcontainer/sandbox-check /usr/local/bin/
```

### sudo

`postCreateCommand` and `postStartCommand` both run as the container user. Both
need root. So a non-root container needs `sudo` without a password.

- A root container needs nothing. Drop `sudo` from the commands.
- A Dockerfile you write installs `sudo` and adds a sudoers file for the user
  with `NOPASSWD:ALL`.
- A reused image with `sudo` and a sudoers entry needs nothing.
- A reused image without `sudo` gets a thin Dockerfile that builds `FROM` the
  project image and adds it. That extends the image. It does not rewrite it.

Without this, `postStartCommand` fails and the container starts with no firewall.

### The firewall

`init-firewall.sh` denies egress by default and allows a short list of hosts.

It needs `NET_ADMIN` and `NET_RAW`, so both go in `runArgs`. The docker daemon
branch replaces both with `--privileged`.

It runs from `postStartCommand`, not `postCreateCommand`. Rules do not survive a
restart.

The script in `files/` already carries the starting allowlist and four fixes.
Read its comments before you change a line of it.

### The allowlist

The script starts with the Anthropic hosts, the npm registry, and GitHub. Add
two groups.

Add the distribution package hosts for the image's package manager.
`postCreateCommand` installs packages from behind this firewall. Debian and
Ubuntu need `deb.debian.org` and `security.debian.org`. Alpine needs
`dl-cdn.alpinelinux.org`.

Add the stack hosts. Add the host that serves the payload, not only the host that
serves the index:

- Go: `proxy.golang.org`, `sum.golang.org`, and `storage.googleapis.com`. The
  proxy redirects module zips to the object store. Without it a build works only
  while every module is already cached, then fails on a dial timeout that names
  nothing.
- Python: `pypi.org` and `files.pythonhosted.org`.
- Rust: `crates.io` and `static.crates.io`.
- Ruby: `rubygems.org`.
- PHP: `packagist.org`.

Name every host you add in the summary.

The allowlist resolves each name once, when the script runs. A host behind a CDN
with names that are not fixed cannot be allowed. Use the off switch for that
task instead.

### The firewall off switch

`sandbox-firewall-off` flushes the rules. It takes no rebuild. The user runs it,
does the one-off task, and restarts the container to get the rules back.

Name it in the summary and in the closing report.

### The check script

`sandbox-check` asserts every fact a broken sandbox breaks. It reads its host
list from `init-firewall.sh`, so the two cannot drift.

The user runs it. `postStartCommand` does not.

Name it in the summary and in the closing report.

## 5. Verify

Offer two steps, and take them only if the user agrees:

1. `devcontainer up --workspace-folder .`
2. `devcontainer exec --workspace-folder . sandbox-check`

Ask first. A build takes minutes.

If the user declines, say that `sandbox-check` runs inside the container after it
opens.

If the check fails, fix the fault it names and run it again.

## 6. Report

Say which files you wrote. Name the off switch and the check script. Tell the
user to reopen the project in the container.

## Limits

Do not build the container without asking.

The firewall raises the cost of a mistake. It is not a boundary against an
adversary. Do not claim more.

Three choices grant more than the minimum, on purpose:

- Credentials mount read-write, so token refresh works.
- The firewall has an off switch, so one-off tasks work.
- All of `~/.claude` mounts, so host skills, settings, and plugins work.

The third has a cost. The sandbox reads host transcripts, host settings, and host
plugins. State it once. Do not ask about it, and do not narrow any of the three.

The docker daemon branch grants a fourth, and only when the user asks for it.

## House style

Write every line in this style. It comes from Simplified Technical English
(ASD-STE100), without the controlled vocabulary.

- One idea per sentence. Keep sentences under 20 words.
- Active voice, present tense.
- One word for one meaning. Do not switch synonyms.
- Define jargon on first use.
- Say what the thing is, not what it is like.
- Prefer the short word to the long one.
- Cut words that carry no meaning.

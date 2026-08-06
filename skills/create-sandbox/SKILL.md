---
name: create-sandbox
description: Write a .devcontainer/ that runs Claude with permission checks off, behind a deny-by-default firewall. Use when the user wants a sandbox, a dev container for Claude, or to run Claude without permission prompts.
---

Write a dev container that runs Claude with permission checks off.

A **sandbox** is a container that limits what Claude reaches. Bypass mode is only safe inside one. So this skill closes the network by default, and mounts one file from the host and nothing else.

Read the project. Ask only what you cannot work out. Show every decision. Wait. Then write the files.

## Process

1. Discover. Read the project before you ask anything.
2. Interview. Ask only what discovery left open.
3. Summarise every decision and wait for the user's word.
4. Write the files.
5. Report what you wrote. Stop.

## 1. Discover

Never ask what you can find out. Look for:

- `Dockerfile`, `docker-compose.yml`, and `compose.yaml` in the project root
- The last `USER` line of any Dockerfile you will use
- The package manager in the image: `apt-get`, `apk`, `dnf`, or none
- Package manifests: `package.json`, `pyproject.toml`, `requirements.txt`, `go.mod`, `Cargo.toml`, `Gemfile`, `composer.json`
- An existing `.devcontainer/`

### The base image

- One Dockerfile and no compose file: reuse it. Use the `build` key.
- A compose file: reuse it. Use the `dockerComposeFile` and `service` keys.
- Neither: pick a base image from the stack. Write a Dockerfile.

Never rewrite an image the project owns. Add Claude, the extension, and the firewall tooling through `postCreateCommand`.

### The user

Read the last `USER` line of the image you will use.

- No `USER` line, or `USER root`: the container runs as root.
- Any other value: the container runs as that user.

## 2. Interview

Ask one question at a time. Wait for the answer.

Give your recommended answer with each question, so the user can reply "yes".

Ask only what changes the shape of the container. Default anything cheap to change.

A single Dockerfile is a decision, not a question. A `USER` line is a decision. A lone `package.json` is a decision. Ask nothing in a project that answers itself.

Ask when:

- A compose file holds several services and none is the obvious host.
- A compose file overrides the user in a way you cannot resolve.
- The image has no package manager you recognise, so you cannot install `iptables` and `ipset`. Offer skipping the firewall as one answer.

## 3. Summarise and wait

Print a summary. List:

- The base image, and whether it comes from the project or is fresh
- The container user, and whether it is root
- The files you will write
- The network allowlist, with every host named
- The mounts

Write nothing until the user confirms.

If the user changes a decision, apply it, print the summary again, and wait again. Repeat as often as the user needs.

If `.devcontainer/` already exists, name the files you would replace. Wait. Do not merge with an existing `devcontainer.json`.

## 4. Write

Write these files:

- `.devcontainer/devcontainer.json`, always
- `.devcontainer/init-firewall.sh`, unless the user skipped the firewall
- `.devcontainer/Dockerfile`, only when the project has no image to reuse

Write no other file. Everything else is created inside the container by `postCreateCommand`.

### devcontainer.json

Use this shape. Swap the image key for the one discovery chose.

```json
{
  "name": "<project> sandbox",
  "build": { "dockerfile": "../Dockerfile", "context": ".." },
  "runArgs": ["--cap-add=NET_ADMIN", "--cap-add=NET_RAW"],
  "remoteUser": "<user>",
  "remoteEnv": { "IS_SANDBOX": "1" },
  "mounts": [
    "source=${localEnv:HOME}/.claude/.credentials.json,target=<home>/.claude/.credentials.json,type=bind"
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

### Bypass mode in the extension

Set both settings keys. The first unlocks the mode. The second selects it for new conversations. One without the other still prompts.

Add `anthropic.claude-code` to the extensions list, so it is there on first open.

### Bypass mode in the shell

Write a shell alias named `claude` that runs `claude --dangerously-skip-permissions`.

Put it in the container user's shell profile from `postCreateCommand`. The console and the extension then behave the same way.

### Root

Claude Code refuses bypass mode as root. The check is exact:

```
permissionMode === "bypassPermissions"
  && process.getuid() === 0
  && process.env.IS_SANDBOX !== "1"
  && process.env.CLAUDE_CODE_BUBBLEWRAP !== "1"
  -> print an error and exit
```

For a root container, set `IS_SANDBOX` to `"1"` in `remoteEnv`. For any other user, leave the variable out.

Use `IS_SANDBOX`. Do not use `CLAUDE_CODE_BUBBLEWRAP`.

### Credentials

Bind-mount the one file `~/.claude/.credentials.json` from the host.

The mount is read-write. Claude refreshes its OAuth token and writes the new one back. A read-only mount forces a login when the token expires.

The target follows the container user. Root gets `/root/.claude/.credentials.json`. A named user gets that user's home directory.

Mount nothing else from `~/.claude`. The container must not read host transcripts, host settings, or the host skills directory.

Docker creates the target's parent directory as root. For a non-root container, `postCreateCommand` must give `~/.claude` back to the container user, or Claude cannot write beside the mount.

### The firewall

`init-firewall.sh` denies egress by default and allows a short list of hosts.

It needs `NET_ADMIN` and `NET_RAW`, so both go in `runArgs`.

It runs from `postStartCommand`, not `postCreateCommand`. Rules do not survive a restart.

The starting allowlist:

- `api.anthropic.com`
- `claude.ai`
- `console.anthropic.com`
- `registry.npmjs.org`
- `github.com`, `api.github.com`, `codeload.github.com`, `objects.githubusercontent.com`

Add what the stack needs. Python gets `pypi.org` and `files.pythonhosted.org`. Go gets `proxy.golang.org` and `sum.golang.org`. Rust gets `crates.io` and `static.crates.io`. Ruby gets `rubygems.org`. PHP gets `packagist.org`.

Name every host you add in the summary.

Use this script as the base:

```sh
#!/usr/bin/env bash
set -euo pipefail

ALLOWED_DOMAINS=(
  api.anthropic.com
  claude.ai
  # ...
)

iptables -F
iptables -X
ipset destroy allowed 2>/dev/null || true
ipset create allowed hash:net

# DNS, loopback, and established traffic come first.
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# The host network reaches the container, so keep it.
HOST_NET=$(ip route | awk '/default/ {print $3}')
iptables -A OUTPUT -d "$HOST_NET" -j ACCEPT
iptables -A INPUT -s "$HOST_NET" -j ACCEPT

for domain in "${ALLOWED_DOMAINS[@]}"; do
  for ip in $(dig +short A "$domain"); do
    [[ $ip =~ ^[0-9.]+$ ]] && ipset add allowed "$ip" -exist
  done
done

iptables -A OUTPUT -m set --match-set allowed dst -j ACCEPT
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

echo "firewall up: ${#ALLOWED_DOMAINS[@]} domains allowed"
```

DNS must be allowed before the default policy drops. The script resolves names at start, so a host that changes address needs a restart.

`postCreateCommand` installs `iptables`, `ipset`, and `dnsutils` with the image's package manager, then copies the script to `/usr/local/bin/init-firewall.sh` and makes it executable.

### The firewall off switch

`postCreateCommand` also writes `/usr/local/bin/sandbox-firewall-off`:

```sh
#!/usr/bin/env bash
set -euo pipefail
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
iptables -F
iptables -X
echo "firewall down. restart the container to bring it back."
```

It takes no rebuild. The user runs it, does the one-off task, and restarts the container to get the rules back.

Name this script in the summary and in the closing report.

## 5. Report

Say which files you wrote. Name the off switch script. Tell the user to reopen the project in the container.

## Limits

Write the files and stop. Do not build the container. Do not start the container.

The firewall raises the cost of a mistake. It is not a boundary against an adversary. Do not claim more.

Two choices grant more than the minimum, on purpose. Credentials mount read-write, so token refresh works. The firewall has an off switch, so one-off tasks work. Do not narrow either one.

## House style

Write every line in this style. It comes from Simplified Technical English (ASD-STE100), without the controlled vocabulary.

- One idea per sentence. Keep sentences under 20 words.
- Active voice, present tense.
- One word for one meaning. Do not switch synonyms.
- Define jargon on first use.
- Say what the thing is, not what it is like.
- Prefer the short word to the long one.
- Cut words that carry no meaning.

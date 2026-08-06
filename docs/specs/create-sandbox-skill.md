# create-sandbox

## Problem Statement

I want to run Claude with permission checks off. That is only safe inside a sandbox. A **sandbox** is a container that limits what Claude reaches.

Writing that container by hand costs time. Each project needs a different base image, a different network allowlist, and a different user. Some of my projects run as root. Some already have their own image, so a fresh base image throws away work.

The two places I start Claude need separate settings. The VSCode extension reads its own settings keys. The container shell reads a command line flag. I have to get both right or one of them still asks me for permission.

I also want the network closed by default. The flag's own warning says to use it only without internet access. But some one-off tasks need the network open, and I do not want to rebuild the container to get it.

## Solution

A `create-sandbox` skill.

It reads the project. It asks me only what it cannot work out. It shows me every decision it made. It waits for my word. Then it writes a `.devcontainer/` directory into the project.

The container it describes starts Claude in bypass mode from both the extension and the shell. It denies network egress by default and allows a short list of hosts. It carries a script that drops the firewall at runtime, so a one-off task needs no rebuild.

## User Stories

1. As a developer, I want to run `create-sandbox` in any project, so that I get a container built for that project.
2. As a developer, I want the skill to read the project first, so that it does not ask me what it can find out.
3. As a developer, I want one question at a time, so that I answer without holding several in my head.
4. As a developer, I want a recommended answer with each question, so that I can reply "yes".
5. As a developer, I want the skill to ask nothing when the project is clear, so that an obvious case costs me one word.
6. As a developer, I want a summary of every decision before any file is written, so that I catch a wrong choice early.
7. As a developer, I want the skill to wait after the summary, so that I can change a decision and see the summary again.
8. As a developer, I want the skill to reuse my project's existing image, so that I keep the tooling the project already installs.
9. As a developer, I want a fresh base image when the project has none, so that a project without Docker still works.
10. As a developer, I want the skill to detect a root container, so that bypass mode is not blocked at start.
11. As a developer, I want the skill to detect a non-root user, so that it mounts files into the right home directory.
12. As a developer, I want the VSCode extension to start in bypass mode, so that the sidebar never asks me for permission.
13. As a developer, I want the extension installed into the container, so that it is there on first open.
14. As a developer, I want a shell alias for bypass mode, so that the console entry point matches the extension.
15. As a developer, I want deny-by-default network egress, so that a permission-free Claude cannot reach anywhere it likes.
16. As a developer, I want a starting allowlist that covers Claude itself, so that the container works before I tune it.
17. As a developer, I want stack-specific hosts added to the allowlist, so that my package manager works.
18. As a developer, I want a script that drops the firewall, so that a one-off task does not need a rebuild.
19. As a developer, I want my host credentials mounted read-write, so that I skip the login and the container writes refreshed tokens back.
20. As a developer, I want only the credentials file mounted, so that the container cannot read my other projects' transcripts.
21. As a developer, I want a warning before the skill overwrites an existing `.devcontainer/`, so that I do not lose a container I wrote.
22. As a developer, I want the skill to write files and stop, so that I control when the container builds.

## Implementation Decisions

### The skill file

Build one skill at `skills/create-sandbox/SKILL.md`.

The frontmatter carries `name` and `description` only. It carries no `model` key. The skill runs on the session model.

The repo installs skills through a symlink from `~/.claude/skills`. The new directory needs no install step.

### The interview

The skill follows the `grill` pattern, which already lives in this repo.

- Discover before each question. Read the repo, the Docker files, and the package manifests.
- Ask one question at a time. Wait for the answer.
- Give a recommended answer with each question.
- Ask only what changes the shape of the container. Default anything cheap to change.

The skill asks nothing it can settle from the repo. A single Dockerfile is a decision. A `USER` line is a decision. A lone `package.json` is a decision.

### The summary gate

After the interview the skill prints a summary and stops. The summary lists:

- The base image, and whether it comes from the project or is fresh
- The container user, and whether it is root
- The files it will write
- The network allowlist
- The mounts

The skill writes nothing until the developer confirms. If the developer changes a decision, the skill applies the change, prints the summary again, and waits again. This repeats as often as the developer needs.

### Detecting the base image

The skill looks for `Dockerfile`, `docker-compose.yml`, and `compose.yaml` in the project root.

- One Dockerfile and no compose file: reuse it through the devcontainer `build` key.
- A compose file: reuse it through the devcontainer `dockerComposeFile` and `service` keys. Ask which service when more than one could host the work.
- Neither: pick a fresh base image from the project's stack, and write a Dockerfile.

A reused image is never rewritten. Claude, the extension, and the firewall tooling arrive through `postCreateCommand`.

### Detecting the user

The skill reads the last `USER` line of the image it will use.

- No `USER` line, or `USER root`: the container runs as root.
- Any other value: the container runs as that user.

Ask only when a compose file overrides the user in a way the skill cannot resolve.

### Root and bypass mode

Claude Code refuses bypass mode when the process runs as root. The check is exact:

```
permissionMode === "bypassPermissions"
  && process.getuid() === 0
  && process.env.IS_SANDBOX !== "1"
  && process.env.CLAUDE_CODE_BUBBLEWRAP !== "1"
  -> print an error and exit
```

For a root container the skill sets `IS_SANDBOX=1` in `remoteEnv`. For a non-root container it omits the variable.

Use `IS_SANDBOX`, not `CLAUDE_CODE_BUBBLEWRAP`. One name for one meaning.

### Bypass mode in the VSCode extension

The skill sets these keys under `customizations.vscode.settings`:

- `claudeCode.allowDangerouslySkipPermissions` set to `true`
- `claudeCode.initialPermissionMode` set to `"bypassPermissions"`

Both keys are needed. The first unlocks the mode. The second selects it for new conversations.

The skill adds `anthropic.claude-code` to `customizations.vscode.extensions`.

### Bypass mode in the container shell

The skill writes a shell alias that runs `claude --dangerously-skip-permissions`.

The alias is named `claude`. The console entry point and the extension then behave the same way.

The alias goes into the container user's shell profile through `postCreateCommand`.

### Credentials

The skill bind-mounts the single file `~/.claude/.credentials.json` from the host.

The mount is read-write. Claude refreshes its OAuth token and writes the new one back to the host. A read-only mount would force a login when the token expires.

The mount target follows the container user. Root gets `/root/.claude/.credentials.json`. A named user gets that user's home directory.

The skill mounts nothing else from `~/.claude`. The container cannot read host transcripts, host settings, or the host skills directory.

### The firewall

The skill writes `.devcontainer/init-firewall.sh`. The script uses `iptables` and `ipset`. It resolves each allowlisted host, adds the addresses to an ipset, allows egress to that set, and drops the rest.

The container needs the `NET_ADMIN` and `NET_RAW` capabilities. The skill adds both to `runArgs`.

The script runs from `postStartCommand`, not `postCreateCommand`. Rules do not survive a container restart, so they are applied on every start.

The starting allowlist covers:

- The Anthropic API host
- The Claude Code OAuth login host
- The npm registry
- GitHub

The skill adds hosts the project's stack needs. A Python project gets the Python package index. A Go project gets the module proxy. The skill states every host it adds in the summary.

`iptables` and `ipset` must be installable in the chosen image. For a reused image the skill checks the package manager the image provides. If it cannot tell, it asks the developer, and offers to skip the firewall as one answer.

### The firewall off switch

The skill writes an executable script into the container that flushes the rules.

The script takes no rebuild and no restart. The developer runs it, does the one-off task, and restarts the container to get the rules back.

The summary and the skill's closing message both name this script.

### Output

The skill writes:

- `.devcontainer/devcontainer.json`, always
- `.devcontainer/init-firewall.sh`, unless the developer skips the firewall
- `.devcontainer/Dockerfile`, only when the project has no image to reuse

If `.devcontainer/` already exists, the skill names the files it would replace and waits. It does not merge with an existing `devcontainer.json`.

The skill writes the files and stops. It does not build the container. It does not start the container. It tells the developer to reopen the project in the container.

## Testing Decisions

This repo holds Markdown skills. It has no test runner, no build step, and no test files. Do not add one. A test framework here would be a bigger change than the feature.

The seam is the skill's output. A **seam** is a place where a test replaces a real part with a fake one. Here the real part is a project, and the fake is a small fixture project.

Verify by running the skill against fixtures and reading what it writes. Test external behaviour, which is the written files and the questions asked. Do not test the wording of the prose.

Cover these cases:

1. A project with no Dockerfile. The skill writes a Dockerfile and a non-root user.
2. A project with a Dockerfile that has no `USER` line. The skill reuses the image, sets `IS_SANDBOX=1`, and mounts credentials at the root home directory.
3. A project with a Dockerfile that sets a named user. The skill reuses the image, omits `IS_SANDBOX`, and mounts to that user's home directory.
4. A project with a compose file and several services. The skill asks which service.
5. A project that already has `.devcontainer/`. The skill warns and waits.

For each case check that `devcontainer.json` carries both extension settings keys, the `anthropic.claude-code` extension, the two capabilities, the credentials mount, and a `postStartCommand` that runs the firewall.

Check that the skill prints a summary and stops before writing.

## Out of Scope

- The `implement` to `lazy` rename. That is a separate change to a separate file.
- The `/spec` handoff removal and the README rewrite. Same reason.
- Building or starting any container.
- Fixing the Docker daemon. It is not running in this WSL2 session, and that is the developer's setup, not the skill's job.
- Firewall support for images with no `apt` and no `apk`. The skill asks instead of solving it.
- Merging into an existing `devcontainer.json`.
- Any credential path other than the single host credentials file.
- Making the sandbox resistant to a Claude that tries to escape it. The firewall raises the cost of a mistake. It is not a security boundary against an adversary.

## Further Notes

The container runs Claude with every permission check off. Every decision in this spec follows from that. When a choice trades convenience for containment, take containment, except where this spec says otherwise.

Two places grant more than the strict minimum, on purpose:

- Credentials mount read-write, so token refresh works.
- The firewall has an off switch, so one-off tasks work.

Both are the developer's explicit choice. Do not narrow them.

The `grill` skill in this repo is the model for the interview and the summary gate. Read it before writing the interview section. Match its structure, not its subject.

House style applies to every line the skill writes and every line of the skill itself. It comes from Simplified Technical English without the controlled vocabulary. One idea per sentence. Sentences under 20 words. Active voice. One word for one meaning.

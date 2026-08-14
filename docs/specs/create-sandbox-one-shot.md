# create-sandbox one-shot

## Problem Statement

The `create-sandbox` skill wrote a container that did not work on the first open. I fixed it by hand in one project, over five commits. Every fix cost a build, a failure, and a hunt.

The failures named nothing useful. My skills vanished inside the container, because `~/.claude/skills` on the host is a symlink to a repository and the link dangled inside. A Go build died on a dial timeout, because the module zips come from a host the allowlist missed. The Docker daemon refused to start twice, for two different reasons. A published port failed with `No chain/target/match by that name`, which points at nothing.

Two of the skill's rules were wrong. It mounts one credentials file and forbids more, so the container has no skills, no settings, and no plugins. It reuses any image the project owns, and my project owns a production image with no toolchain in it.

I want the next sandbox to work when I open it. When it does not, I want one message that names the fault.

## Solution

Rewrite the skill from the fixes that made a real container work.

The skill becomes a directory. `SKILL.md` holds the process and the decisions. The scripts become real files the skill copies into the project, so a fix survives verbatim instead of being retyped. The Docker daemon branch moves to a reference file, so it costs nothing in a project that does not need it.

The container gains `sandbox-check`. It asserts every fact the five commits found, in order, and names what failed.

The skill stops being forbidden from building. It offers to build the container and run the check.

## User Stories

1. As a developer, I want my host skills to work inside the sandbox, so that the container has the same skills as the host.
2. As a developer, I want every symlink under `~/.claude` to resolve inside the container, so that no linked directory dangles.
3. As a developer, I want my host settings and plugins in the sandbox, so that the container behaves like my host session.
4. As a developer, I want the skill to state what the full mount exposes, so that I know the cost I accepted.
5. As a developer, I want the skill to reject a production image, so that I do not get a container with no toolchain.
6. As a developer, I want the skill to ignore a compose file of backing stores, so that it does not ask me which database hosts my work.
7. As a developer, I want a fresh image to carry my own uid, so that files in the workspace keep their owner.
8. As a developer, I want no recursive `chown` when the uid already matches, so that the container does not walk my host home directory.
9. As a developer, I want the firewall script to survive a second run, so that re-running it does not starve its own name lookups.
10. As a developer, I want the firewall to allow the whole container subnet, so that a `/16` bridge is not half blocked.
11. As a developer, I want the firewall to fail loudly when it cannot read the subnet, so that it does not lock me out quietly.
12. As a developer, I want the allowlist to cover the hosts that serve package payloads, so that a build does not time out on a redirect.
13. As a developer, I want an opt-in Docker daemon inside the sandbox, so that integration tests run.
14. As a developer, I want the skill to detect that my tests need Docker, so that it offers the branch without me knowing to ask.
15. As a developer, I want the daemon branch to state its cost, so that I know `--privileged` is wider than the firewall needs.
16. As a developer, I want the daemon to pick a storage driver that works, so that it starts on an overlay root filesystem.
17. As a developer, I want to know the daemon starts after the firewall, so that publishing a port does not fail.
18. As a developer, I want to know images cannot be pulled through the firewall, so that I pull once with it down instead of debugging it.
19. As a developer, I want a check script in the container, so that a broken sandbox tells me which part is broken.
20. As a developer, I want the check to prove a blocked host is blocked, so that I trust the firewall is up.
21. As a developer, I want the check to test every allowlisted host, so that a missing host is found before a build needs it.
22. As a developer, I want the skill to offer to build the container, so that I learn it works without a manual round trip.
23. As a developer, I want the skill to ask before it builds, so that a multi-minute build is my choice.
24. As a developer, I want the scripts shipped as files, so that the agent copies them instead of retyping them.
25. As a developer, I want the Docker branch in its own file, so that it stays out of context when I do not use it.

## Implementation Decisions

### The skill directory

The skill grows from one file to a directory.

- `SKILL.md` holds the process, the decisions, the allowlist, and the summary rules.
- A `files/` directory holds `init-firewall.sh`, `sandbox-check`, and `start-docker`.
- A `reference/` directory holds one file for the Docker daemon branch.

The skill copies from `files/` into the project. It does not retype a script. `SKILL.md` names its own directory as the source.

`grill`, `spec`, and `lazy` stay single-file. `create-sandbox` is the only skill that ships artifacts, so it is the only one with a directory.

The frontmatter keeps `name` and `description` only. It carries no `model` key.

### The source of the scripts

A working container exists at `~/palver/nucleus/.devcontainer/`. Its `init-firewall.sh` and `start-docker` are correct and tested. Copy them into `files/` and generalise them.

Generalising means removing what belongs to that one project. The Go module hosts, the Debian package hosts, and the image registry hosts become entries the skill adds by rule, not fixed lines. The comments that record a fault stay, because they are the reason the line exists.

### The mounts

Mount all of `~/.claude` from the host, read-write. The single credentials file is no longer the rule.

Before writing the mounts, resolve every symlink directly under `~/.claude`. For each link that points outside `~/.claude` at an absolute host path, add a second bind mount. Its source and its target are that same absolute path. The link then resolves on both sides.

Do not rewrite the symlink. The host shares it.

Do not hardcode any specific path. Read the links at write time.

Set `workspaceFolder` and `workspaceMount` explicitly. The workspace target is `/workspace`.

The cost is stated in the skill, once, as a limit: the sandbox reads host transcripts, host settings, and host plugins. It is not asked as a question, because the answer never changes.

### Choosing the image

A project image is reused only when it is a development image. A **development image** carries the language toolchain in its final stage and expects the source tree as its workspace.

Reject a project image when any of these is true:

- It is a multi-stage build whose final stage is a slim or distroless image.
- Its final stage copies built artefacts in and holds no compiler.
- Its `ENTRYPOINT` or `CMD` runs the application.

Reuse a compose file only when a service builds the project's own source. A compose file of databases, queues, and caches is not a dev host. The sandbox reaches those services over the network instead. Do not ask which service to use when no service builds the source.

When no image qualifies, write a Dockerfile from the stack's official toolchain image.

### The container user

Read the host uid and gid during discovery. Write those numbers literally into a fresh Dockerfile, and create the user with them.

A matching uid means files in the bind-mounted workspace keep their owner. It also removes the recursive `chown` of the home directory, which would otherwise walk the host's real `~/.claude`.

Keep a `chown` only when the uid cannot match.

For a reused image, read the last `USER` line, as before. A root container gets `IS_SANDBOX=1` in `remoteEnv`. A named user gets no such variable.

### sudo

Both lifecycle commands run as the container user, and both need root. A non-root container therefore needs `sudo` without a password. The old skill never said so, and a container that lacks it starts with no firewall.

A Dockerfile the skill writes installs `sudo` and grants the user `NOPASSWD:ALL`. A reused image that lacks `sudo` gets a thin Dockerfile built `FROM` the project image, which adds it. That extends the image rather than rewriting it, so the reuse rule holds.

### The firewall script

Four corrections apply to the script the old skill carried. Each one is a fault that was found by running it.

1. Reset the three default policies to `ACCEPT` before flushing. A flush leaves policies alone, so a second run inherits `DROP` and starves its own name lookups.
2. Create the ipset with an `-exist` flag and then flush it. Do not depend on destroying it, because the set survives a chain flush.
3. Read the container subnet as a CIDR from the kernel route, not as the default gateway address. The Docker bridge is commonly a `/16`, so a `/24` assumed around the gateway drops part of it.
4. Exit with an error when the subnet cannot be read. Leave the firewall down and say so, rather than applying rules that lock the container out.

Accept loopback on input as well as output.

The script still runs from `postStartCommand`. Rules do not survive a restart.

The script needs four packages, and the skill must name all four. The old skill named three and missed the one that provides `ip`. The script then fails with `ip: command not found` on any reused image.

### The allowlist

The starting list gains two groups beyond the old one:

- The error reporting host Claude Code contacts.
- The distribution package hosts for the image's package manager, because `postCreateCommand` installs packages behind the firewall.

Do not carry `statsig.anthropic.com` from the source container. The name has no A record, so the firewall adds nothing for it. A dead entry looks like an allowed host and is not one.

The check treats a name with no A record as its own fault, separate from a host the firewall drops. The two need different fixes.

Stack hosts follow a rule the old skill missed. Add the host that serves the package payload, not only the host that serves the index. A Go project needs the module proxy and the object store the proxy redirects to. Without the second one, a build works only while every module is already cached, and then fails on a dial timeout that names nothing.

State every host in the summary.

### The Docker daemon branch

The branch is opt-in. It is never a default.

Detect the need during discovery. A container-based test library in a manifest is the signal. A test suite that starts containers is the signal. When the signal is present, ask. When it is absent, say nothing.

When the developer declines, the container is unchanged.

When the developer accepts, write these decisions:

- `runArgs` carries `--privileged`, which replaces `--cap-add=NET_ADMIN` and `--cap-add=NET_RAW`. State the cost: the container gets the host kernel's full surface. It still cannot reach the host daemon, so it cannot start containers on the host or mount the host filesystem.
- The host Docker socket is never mounted. That grants root on the host to a permission-free Claude, which is the one thing the sandbox prevents.
- Rootless Docker is blocked on WSL2. One line records that, not the post-mortem.
- Install Docker from the static archive, not the distribution package, because the package brings a service the container cannot run. The archive extraction must include the userland proxy and the init binary. Without the proxy the daemon refuses to start, and published ports need it.
- The daemon does not start with the container. `start-docker` starts it, so a session that runs no integration test pays nothing.
- `start-docker` picks the storage driver by reading the filesystem type under the daemon's data directory. An overlay filesystem cannot stack another overlay on itself, so it selects the copying driver instead. An environment variable overrides the choice.
- Start the daemon after the firewall. The firewall flushes every chain, including the one the daemon creates, so a container that publishes a port then fails with a message that names no chain. Re-running the firewall does it again, so restart the daemon after.
- Images cannot be pulled through the firewall. The registry hosts get the manifest and the auth token. The layers come from a CDN on hostnames a resolved-once ipset cannot predict. Pull once with the firewall down, then bring it back.

The image registry hosts belong to this branch's allowlist only.

Do not carry a decision to disable the test reaper. That is one project's judgment.

### The check script

The skill always writes `sandbox-check` and installs it into the container's local binary directory, the same way it installs the firewall off switch.

The developer runs it. `postStartCommand` does not.

It runs these assertions in order, and it names the one that failed:

1. The Claude Code CLI answers a version query.
2. The bypass alias is in the container user's shell profile.
3. The credentials file is readable and writable.
4. Every symlink under `~/.claude` resolves.
5. `IS_SANDBOX` is `1` when the container runs as root, and absent otherwise.
6. An allowlisted host answers.
7. A host that is not allowlisted is refused.
8. Every host in the allowlist answers.
9. With the Docker branch on: the daemon answers, and a container that publishes a port starts.

Assertion 4 catches the fault that started this rewrite. Assertion 8 catches a missing package host before a build times out on it.

The script reads its host list from the firewall script, so the two cannot drift.

### Building

The old limit said the skill must not build the container. It now must not build without asking.

After writing the files, the skill offers two steps: bring the container up, then run the check inside it. It does this only when the developer agrees.

The process gains a verification step before the report. The report names the files written, the off switch, and the check script.

## Testing Decisions

This repo holds Markdown skills. It has no test runner and no test files. Do not add one.

The seam is the skill's output. A **seam** is a place where a test replaces a real part with a fake one. The real part is a project. The fake is a small fixture project.

Verify by running the skill against fixtures and reading what it writes. Test the written files and the questions asked. Do not test the wording of the prose.

Cover these cases:

1. A project whose only image is a production multi-stage build. The skill writes a fresh Dockerfile and does not reuse the project image.
2. A project whose compose file holds only backing stores. The skill asks nothing about services.
3. A host whose `~/.claude/skills` is a symlink to a repository. The written mounts include the link's target at its own absolute path.
4. A project with a container-based test library. The skill offers the Docker branch and states its cost.
5. A project with no such library. The skill does not mention Docker.
6. A project that already has `.devcontainer/`. The skill names the files it would replace and waits.

For each case, check that `devcontainer.json` carries both extension settings keys, the `anthropic.claude-code` extension, the full `~/.claude` mount, an explicit workspace mount, and a `postStartCommand` that runs the firewall.

Check that the copied `init-firewall.sh` carries all four corrections.

Check that the skill prints a summary and waits before writing, and asks before building.

The existing spec at `docs/specs/create-sandbox-skill.md` holds the cases the first version covered. The cases above are additions, not replacements.

## Out of Scope

- Changes to `grill`, `spec`, `lazy`, and the README.
- Rewriting the existing spec. It stays as the record of the first version.
- Merging into an existing `devcontainer.json`.
- Firewall support for an image with no package manager the skill recognises. It still asks, and still offers to skip the firewall.
- Rootless Docker. The kernel refuses it here, and one line records that.
- Making an ipset track a CDN. It cannot be done, so the workflow works around it.
- Making the sandbox resistant to a Claude that tries to escape it.

## Further Notes

Every decision here comes from a fault found by running a real container. The five commits behind `~/palver/nucleus/.devcontainer/` are the record. Read them before changing a decision in this spec.

The container runs Claude with every permission check off. When a choice trades convenience for containment, take containment, except where this spec says otherwise.

Three places grant more than the strict minimum, on purpose:

- Credentials mount read-write, so token refresh works.
- The firewall has an off switch, so one-off tasks work.
- The whole of `~/.claude` mounts, so host skills and settings work.

The Docker branch grants a fourth, and only when the developer asks for it.

House style applies to every line the skill writes and every line of the skill itself. One idea per sentence. Sentences under 20 words. Active voice. One word for one meaning.

# Working in this repo

## Commits

Use Conventional Commits. The subject line is:

```
<type>(<scope>): <description>
```

- `type` is one of: `feat`, `fix`, `docs`, `refactor`, `chore`.
- `scope` is the skill name, such as `grill` or `spec`. Leave it out for repo-wide changes.
- `description` is imperative and lower case. No full stop. Under 72 characters.

Add `!` after the type for a breaking change, and explain it in the body.

Examples:

```
feat(spec): write specs to docs/
fix(grill): stop re-asking after confirmation
docs: record the install step
chore: ignore agent state files
```

## Identity

Do not pass `-c user.name` or `-c user.email` to git. The global config is correct.

## Style

Prose in this repo follows the house style in `skills/grill/SKILL.md`.

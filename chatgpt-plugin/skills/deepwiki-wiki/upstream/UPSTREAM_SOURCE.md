# Upstream source of truth

This ChatGPT package is an additive runtime adapter. The original Agent Skill remains the canonical source of truth in the repository's `main` branch and must remain byte-for-byte unchanged:

- Repository: https://github.com/my-ai-skill/deepwiki-skill
- Default branch: `main`
- Core skill: `.apm/skills/wiki/SKILL.md`
- Phase specifications: `.apm/skills/wiki/references/workflow/`
- Policies and templates: `.apm/skills/wiki/references/` and `.apm/skills/wiki/templates/`
- Python helpers: `.apm/skills/wiki/scripts/`
- Original worker definition: `.apm/agents/workflow-runner.agent.md`
- Original command prompt: `.apm/prompts/gen-wiki.prompt.md`
- Original manifest: `apm.yml`

The plugin feature branch must be created from `main` and add this package under `chatgpt-plugin/`. Do not edit, rename, or delete any upstream `.apm/` content or `apm.yml`. The branch will therefore retain the complete original Skill as an unchanged backup and add this platform-specific distribution folder.

The exact upstream commit inspected during the initial adaptation was `887304e68ff3711a964bcb4b3f33e47ad53c4405`. Re-check and pin the actual parent SHA at branch-creation time.

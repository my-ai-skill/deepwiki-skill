# Upstream dependency bootstrap

The installed plugin intentionally keeps the original DeepWiki source-of-truth in `my-ai-skill/deepwiki-skill`; it does not duplicate the original implementation. The runtime adapter must resolve the exact upstream files before executing a phase.

- Pinned upstream commit: `887304e68ff3711a964bcb4b3f33e47ad53c4405`
- Repository: https://github.com/my-ai-skill/deepwiki-skill
- Skill root: `.apm/skills/wiki/`
- Worker: `.apm/agents/workflow-runner.agent.md`

The phase-specific paths and the stop-on-missing-dependency rule are defined in `workflow-runner-contract.md`. If the host has neither the local upstream source nor a GitHub reader, report `BLOCKED: upstream phase specification unavailable`. Do not invent a phase specification and do not write partial Wiki output.

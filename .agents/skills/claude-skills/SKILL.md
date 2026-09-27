---
name: claude-skills
description: Master catalog router for 731+ skills and agents categorized via AgenticSkills.io 16-category taxonomy on demand.
---

# Claude Skills & AgenticSkills Dynamic Catalog Router

Provides on-demand access to **731+ specialized skills and 116 agent personas** indexed cleanly under the **AgenticSkills.io 16-Category Taxonomy** without bloating the active LLM context window:

## 1. AgenticSkills.io 16-Category Taxonomy

All 731 catalog items are mapped into the official 16 AgenticSkills categories:

| Category Key | Category Title | Items | Core Description |
|---|---|---|---|
| `web-development` | Web Development | 46 | Frontend frameworks, React, Next.js, and modern web tooling |
| `backend` | Backend & APIs | 24 | Server-side development, databases, and API integration patterns |
| `devops` | DevOps & Infrastructure | 45 | Deployment, CI/CD, cloud infrastructure, and automation |
| `testing` | Code Quality & Testing | 75 | Testing methodologies, debugging, code review, and quality assurance |
| `ai-ml` | AI/ML Development | 102 | Machine learning, model training, AI research, and generative AI |
| `data-science` | Data Science | 28 | Data visualization, scientific computing, and analytics |
| `marketing` | Content & Marketing | 32 | Copywriting, content strategy, and marketing automation |
| `seo` | SEO & Growth | 25 | Search engine optimization, GEO/AEO, analytics, and growth strategies |
| `design` | Design & UI/UX | 137 | UI design systems, accessibility, and user experience patterns |
| `productivity` | Productivity | 44 | Workflow optimization, ideation, and developer productivity tools |
| `documents` | Document Creation | 11 | PDF generation, documentation, and structured content creation |
| `security` | Security | 35 | Security auditing, static analysis, and vulnerability detection |
| `database` | Database | 19 | Database optimization, migrations, and data modeling |
| `mobile` | Mobile Development | 14 | React Native, iOS, Android, and cross-platform development |
| `agents` | Agent Architecture | 101 | Multi-agent systems, MCP servers, and agent orchestration |
| `official` | Official Partners | 118 | Skills from official platform teams (Vercel, Microsoft, AWS, Hugging Face, etc.) |

## 2. Querying the Dynamic Catalog CLI

Use `query_catalog.py` with `rtk` to search, filter by category, or inspect full documentation on-demand:

```powershell
# List all 16 categories with item counts and descriptions
rtk python .agents/plugins/claude-skills/query_catalog.py --categories

# Filter by AgenticSkills category (e.g. web-development, backend, devops, design, testing, etc.)
rtk python .agents/plugins/claude-skills/query_catalog.py --category web-development
rtk python .agents/plugins/claude-skills/query_catalog.py --category design
rtk python .agents/plugins/claude-skills/query_catalog.py --category official

# Keyword search across IDs, names, descriptions, and authors
rtk python .agents/plugins/claude-skills/query_catalog.py --search "<term>"

# Inspect full markdown documentation, author, rank, platforms, and install command
rtk python .agents/plugins/claude-skills/query_catalog.py --inspect taste-skill
rtk python .agents/plugins/claude-skills/query_catalog.py --inspect supabase-postgres

# Show complete catalog overview & statistics
rtk python .agents/plugins/claude-skills/query_catalog.py --stats
```

## 3. Mapping to MaxIM 9 Consolidated Master Skills

The 16 AgenticSkills categories map onto MaxIM's 9 core active skills as follows:

| AgenticSkills Category | Primary MaxIM Master Skill | Primary MaxIM Specialized Agent |
|---|---|---|
| `web-development`, `design` | `react-and-web-design` | `expert-react-frontend-engineer`, `ui-ux-designer` |
| `seo` | `react-and-web-design` (Section 8: OpenSEO) | `search-specialist`, `agency-brand-guardian` |
| `backend`, `database` | `code-architect` + `llm-and-rag-engineering` | `backend-architect`, `database-architect` |
| `devops`, `agents` | `agent-architecture` + `agency-agents` | `multi-agent-coordinator`, `mcp-expert` |
| `testing`, `security` | `code-quality-guardian` + `test-engineering` | `test-generator`, `se-security-reviewer` |
| `ai-ml`, `data-science` | `llm-and-rag-engineering` + `graphify` | `llm-architect`, `agency-ai-engineer` |
| `marketing` | `voice-agents` + `voice_studio` | `prompt-engineer`, `agency-whimsy-injector` |
| `productivity`, `documents` | `project-orchestrator` + Obsidian Ops | `planner`, `obsidian-connection-agent` |
| `mobile` | `react-and-web-design` + `adb_tool` | `agency-frontend-developer` |
| `official` | `claude-skills` (Dynamic Catalog Router) | `project-orchestrator` |

## 4. Integrated Skill Doctor (`skill-doctor`)
- **Authoring Standards**: Every skill must have valid YAML frontmatter, under 70 chars description, clear triggers, and actionable workflows.
- **Linting & Grading**: Grade skills against real conversation history; repair stale references, bloated prompts, or ambiguous triggers.

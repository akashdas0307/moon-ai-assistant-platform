# Agents Directory

This directory contains all agent definitions for the Moon-AI system.

## Structure

```
agents/
└── head-agent/          # Primary agent
    ├── AGENT.md         # Capabilities and rules
    ├── SOUL.md          # Personality and ethics
    ├── USER.md          # User profile (auto-generated)
    ├── NOTEBOOK.md      # Working memory
    ├── SPARK.md         # Heartbeat configuration
    └── spark_logs/      # SPARK activity logs
```

## Core Files Explained

### AGENT.md
Defines what the agent can do, its available tools, operating rules, and boundaries.
Loaded as system context for every agent interaction.

### SOUL.md
Defines how the agent communicates, its personality traits, ethical framework, and
decision-making principles. Shapes the agent's behavior and tone.

### USER.md
Automatically populated file that stores learned information about the user's
preferences, communication style, and context. Updated after every 5 conversations.

### NOTEBOOK.md
The agent's working memory. The agent writes notes to itself here about pending
tasks, important context, and things to remember. Checked by SPARK heartbeat.

### SPARK.md
Immutable configuration file for the autonomous heartbeat system. Defines how
often the agent should wake up to check for pending tasks.

## File Lifecycle

1. **Initialization:** Core files (AGENT, SOUL, SPARK) are created once
2. **Runtime:** USER and NOTEBOOK files are updated during agent operation
3. **Persistence:** All files persist across restarts
4. **Immutability:** AGENT, SOUL, and SPARK should rarely change (manual only)
5. **Auto-Update:** USER and NOTEBOOK are automatically managed by the agent

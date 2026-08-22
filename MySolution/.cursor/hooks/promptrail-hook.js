#!/usr/bin/env node
// Promptrail hook script — captures Cursor agent events for
// per-prompt file tracking, response viewing, and edit-based rollback.
//
// Writes directly to the shadow DB (.promptrail/promptrail.db) via node:sqlite.
// Requires Node 22.5+ (the current LTS).

const { readFileSync, mkdirSync } = require("fs");
const { join } = require("path");

const TRACKED_EVENTS = new Set([
  "afterFileEdit",
  "beforeSubmitPrompt",
  "afterAgentResponse",
  "stop",
]);

const HOOK_SCHEMA = `
  CREATE TABLE IF NOT EXISTS hook_prompts (
    conversationId TEXT NOT NULL,
    generationId   TEXT NOT NULL,
    promptText     TEXT NOT NULL,
    model          TEXT,
    timestamp      REAL NOT NULL,
    PRIMARY KEY (conversationId, generationId)
  );
  CREATE TABLE IF NOT EXISTS hook_edits (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversationId  TEXT NOT NULL,
    generationId    TEXT NOT NULL,
    filePath        TEXT NOT NULL,
    oldString       TEXT,
    newString       TEXT,
    timestamp       REAL NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_hook_edits_gen
    ON hook_edits(conversationId, generationId);
  CREATE TABLE IF NOT EXISTS hook_responses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversationId  TEXT NOT NULL,
    generationId    TEXT NOT NULL,
    responseText    TEXT NOT NULL,
    model           TEXT,
    timestamp       REAL NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_hook_responses_gen
    ON hook_responses(conversationId, generationId);
`;

try {
  const input = readFileSync(0, "utf-8");
  const event = JSON.parse(input);

  if (!TRACKED_EVENTS.has(event.hook_event_name)) process.exit(0);

  const wsRoot =
    (event.workspace_roots && event.workspace_roots[0]) ||
    process.env.CURSOR_PROJECT_DIR;
  if (!wsRoot) process.exit(0);

  const dir = join(wsRoot, ".promptrail");
  mkdirSync(dir, { recursive: true });

  const { DatabaseSync } = require("node:sqlite");
  const db = new DatabaseSync(join(dir, "promptrail.db"));
  db.exec("PRAGMA journal_mode=WAL");
  db.exec(HOOK_SCHEMA);

  const convId = event.conversation_id || "";
  const genId = event.generation_id || "";
  const model = event.model || null;
  const now = Date.now();

  switch (event.hook_event_name) {
    case "beforeSubmitPrompt": {
      db.prepare(
        `INSERT OR REPLACE INTO hook_prompts
         (conversationId, generationId, promptText, model, timestamp)
         VALUES (?, ?, ?, ?, ?)`
      ).run(convId, genId, event.prompt || "", model, now);
      break;
    }

    case "afterFileEdit": {
      const filePath = event.file_path || "";
      const relPath = filePath.startsWith(wsRoot + "/")
        ? filePath.slice(wsRoot.length + 1)
        : filePath;
      const edits = Array.isArray(event.edits) ? event.edits : [];
      const stmt = db.prepare(
        `INSERT INTO hook_edits
         (conversationId, generationId, filePath, oldString, newString, timestamp)
         VALUES (?, ?, ?, ?, ?, ?)`
      );
      if (edits.length === 0) {
        stmt.run(convId, genId, relPath, null, null, now);
      } else {
        for (const edit of edits) {
          stmt.run(
            convId, genId, relPath,
            edit.old_string ?? null,
            edit.new_string ?? null,
            now
          );
        }
      }
      break;
    }

    case "afterAgentResponse": {
      db.prepare(
        `INSERT INTO hook_responses
         (conversationId, generationId, responseText, model, timestamp)
         VALUES (?, ?, ?, ?, ?)`
      ).run(convId, genId, event.text || "", model, now);
      break;
    }

    case "stop": {
      // no-op for now; presence of hook_prompts without matching stop
      // means the prompt is still running
      break;
    }
  }

  db.close();
} catch {
  // Never fail — hooks must be transparent to the user
}

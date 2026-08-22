---
name: brittle-logic-repair
description: >-
  Use this skill to systematically discover, rank, and repair brittle error handling 
  (e.g., bare `except Exception:` in Python, `.unwrap()` in Rust) across a codebase.
---

# Brittle Logic Repair Workflow

This skill outlines the process for diagnosing and fixing brittle logic that bypasses safety guarantees in a codebase.

## 1. Discovery
Use `grep_search` to find bypassed safety guarantees across the target directory:
- **Python**: Search for `except Exception:` to find swallowed exceptions.
- **Rust**: Search for `\.unwrap\(\)|\.expect\(` to find explicit panics.

## 2. Hitlist Generation
Rank the files by the number of occurrences. Present a prioritized "Hitlist" to the user, categorized by severity. Focus on bridging code and core engine logic as CRITICAL severity, and UI automation or data parsing as HIGH severity.

## 3. Surgical Refactoring (Scripted)
Do not use file modification tools (like `multi_replace_file_content`) for bulk refactoring of 100+ instances, as it is prone to indentation errors and context loss. 
Instead, utilize the provided Python scripts in `[scripts/](./scripts)` to execute AST/Regex-based bulk replacements securely.

### Rust-Specific Context Injection
> [!CAUTION]
> **Critical Rust Context Lesson:** When replacing `.unwrap()` with `?` in Rust tests using the `anyhow` crate, you MUST inject `use anyhow::Context;` specifically *inside* the `mod tests { ... }` block. Global file imports will not cascade into the test module correctly, leading to `trait not satisfied` compiler errors.

To execute the scripted refactorings:
1. Copy the relevant template from `scripts/` to a scratch directory.
2. Modify the target file paths inside the script.
3. Run the script via the command line.

## 4. Validation
Verify the changes using standard compilation and test tools:
- **Python**: Run `pytest` or `python -m compileall`.
- **Rust**: Run `cargo check --tests`.

# Lab 5 — Static Code Analysis

**Script analysed:** `support_ticket_tracker.py`
**Tools:** Pylint 4.1.3, Bandit 1.9.4, Flake8 7.4.1 (Python 3.13)

## Summary of results

| Tool | Before | After |
|---|---|---|
| Pylint | 5.00 / 10 | **10.00 / 10** |
| Bandit | 2 issues (1 Medium, 1 Low) | **0 issues** |
| Flake8 | 12 violations | **0 violations** |

Full tool output is kept in `reports/before/` and `reports/after/`.

## How to reproduce

```bash
python3 -m venv venv
source venv/bin/activate
pip install pylint bandit flake8

pylint support_ticket_tracker.py > pylint_report.txt
bandit -r support_ticket_tracker.py > bandit_report.txt
flake8 support_ticket_tracker.py  > flake8_report.txt
```

## Identified issues and fixes

| # | Issue | Type | Tool / Code | Line(s) | Description | Fix approach |
|---|---|---|---|---|---|---|
| 1 | Use of `eval()` | **Security (Medium)** | Bandit B307 | 92 | `eval("print('unsafe demo')")` ran a string through the interpreter. If the string ever came from config, user input or the environment, it would be arbitrary code execution (CWE-78). | Deleted `eval()` and called `print("demo mode")` directly. Nothing needed dynamic evaluation in the first place. |
| 2 | `try/except/pass` with a bare `except` | **Security (Low) / Bug** | Bandit B110, Pylint W0702, Flake8 E722 | 24–25 | A bare `except` swallowed *every* exception, including `KeyboardInterrupt` and typos, and `pass` discarded it silently, so a failed assignment looked identical to a successful one. | Narrowed to `except KeyError`, the only error the lookup can raise, and logged a warning before returning `False`. |
| 3 | Mutable default argument | **Bug** | Pylint W0102 | 10 | `audit_log=[]` is evaluated once at definition time, so the *same* list is shared by every call that omits the argument — entries accumulate across unrelated calls. | Defaulted to `None` and created a fresh list inside the function. |
| 4 | Too many arguments | Design | Pylint R0913, R0917 | 10 | `create_ticket` took 6 parameters (5 positional max), making call sites order-sensitive and easy to get wrong. | Grouped the ticket fields into a `TicketRequest` dataclass, reducing the signature to `create_ticket(request, audit_log=None)`. |
| 5 | Files opened without `with` / encoding | Bug | Pylint R1732, W1514 | 46, 53 | `open()` without a context manager leaks the handle if an exception is raised mid-write, and an unspecified encoding makes behaviour platform-dependent. | Rewrote both helpers with `with open(..., encoding="utf-8")` and `json.dump` / `json.load`. |
| 6 | `global` statement | Design | Pylint W0603 | 52 | `load_tickets` rebound the module-level `TICKETS` name, so any other module holding a reference kept the stale dictionary. | Mutated in place with `TICKETS.clear()` + `TICKETS.update(loaded)`; the `global` declaration is gone. |
| 7 | Comparison to `None` with `!=` | Style | Pylint C0121, Flake8 E711 | 37 | `status != None` relies on `__ne__` rather than identity. | Changed to `status is not None` (and made the `priority` check symmetric). |
| 8 | Non-snake_case function name | Style | Pylint C0103 | 66 | `closeTicket` broke PEP 8 naming, inconsistent with every other function in the file. | Renamed to `close_ticket` and updated the caller. |
| 9 | Unused imports and variables | Dead code | Pylint W0611/W0612/W0613, Flake8 F401/F841 | 4, 5, 20, 84 | `sys` and `random` were never used, `count` was assigned and discarded, and the `notify` parameter was never read. | Removed all four. |
| 10 | Missing docstrings | Maintainability | Pylint C0114, C0116 | module + 9 functions | No module or function documentation. | Added a module docstring and a one- to three-line docstring per function. |
| 11 | Long lines and trailing whitespace | Formatting | Flake8 E501/W291, Pylint C0301/C0303 | 10, 14, 63, 71, 79, 80, 84 | Lines up to 176 characters, plus trailing whitespace. | Exploded the ticket dictionary over multiple lines, wrapped the `TicketRequest` calls, stripped the whitespace — everything now fits in 79 columns. |
| 12 | Eager f-string in logging | Performance | Pylint W1203 | 85 | `logging.info(f"...")` formats the string even when the log level would discard it. | Switched to lazy `%s` interpolation: `logging.info("Tickets created: %s", len(TICKETS))`. |
| 13 | Verbose conditionals | Readability | Pylint C1802, R1703, R1705 | 60, 71–74 | `if not len(TICKETS)` instead of truthiness, and an `if/else` that only returned `True`/`False`. | Used `if not TICKETS:` and `return ticket["status"] in ("open", "in_progress")`. |

### Extra robustness (not tool-reported)

`update_status` and `is_open` used to raise `KeyError` on an unknown id — reachable from the `input()` prompt in `main()`. Both now look the ticket up with `.get()` and fail gracefully.

## Commits

| Commit | Scope |
|---|---|
| `9c5b62f` | `fix(bandit)` — removed `eval()`, replaced the bare `except`/`pass`; adds `reports/before/` |
| `7810d1c` | `refactor(pylint)` — docstrings, mutable default, dataclass, `with`/encoding, no `global`, renames, dead code |
| `d4a0803` | `style(flake8)` — wrapped the remaining long lines; adds `reports/after/` |

## Reflection

*(The handout refers to reflection questions; the questions themselves were not printed in the PDF, so these answer the standard set implied by the learning outcomes.)*

**1. What is static analysis, and what did each tool contribute?**
Static analysis inspects source code without running it, so it finds defects on paths that testing may never exercise. The three tools did not overlap much by accident — they answer different questions. Bandit asked *is this dangerous?* and found the `eval()` call and the silently swallowed exception. Pylint asked *is this correct and well-designed?* and found the real bug of this script, the shared mutable default. Flake8 asked *does this read like Python?* and found the formatting noise. Running only one would have left two whole categories unexamined.

**2. Which issue was the most serious, and why?**
The `eval()` call, rated Medium by Bandit. Its argument was a hard-coded literal, so the program as written was not actually exploitable — but the *pattern* is one refactor away from arbitrary code execution, and it was gated behind an environment variable, which is exactly the kind of switch that gets flipped in a deployed environment. The mutable default argument was the most *likely* to cause a real-world defect: it produces a data-corruption bug that is intermittent, invisible in a single run, and notoriously hard to reproduce.

**3. Were any findings false positives?**
None were strictly wrong, but severity did not map onto risk. `try/except/pass` is rated Low by Bandit, yet it was arguably the more dangerous of the two security findings, since it hid failures from the operator. Conversely, `too-many-arguments` is a style opinion rather than a defect — six parameters is legal and works fine; fixing it was a judgement call about readability, not a correction. Tool severity is a starting point for triage, not a verdict.

**4. How does static analysis contribute to code quality and maintainability?**
It makes a class of review feedback automatic and consistent. A reviewer who has to point out trailing whitespace has less attention left for the mutable default argument; linting in CI removes the first conversation entirely. It also encodes conventions that would otherwise live only in people's heads, which matters most when a codebase is handed between developers.

**5. What are its limits?**
Static analysis checks form, not intent. Every tool here passed the script with a perfect score while it still stores tickets in a module-level global, has no tests, and silently overwrites `tickets.json` on every run — none of which a linter can see. A clean report means no *known patterns* matched; it is not evidence the program is correct. Chasing a perfect score can also make code worse, by rewarding suppression comments and arbitrary refactors over genuine clarity.

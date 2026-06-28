"""RHCLOUD V1 — backend kernel package (Developer A scope).

Layout (A-owned modules):
    builder.py        Prompt Builder (whitelist substitution, [修正-3])
    manager.py        Provider Manager (dynamic load by site, §6.3)
    validation.py     Config / pipeline validation (A5, §6.1.2)
    runtime.py        Execution engine (structured StepResult, retry,
                      Profile lock, event push, persistence; [修正-1/4/8])
    cleanup.py        Session retention cleanup (A8, NFR-09, 14 days)
    logging_conf.py   Structured JSON logging + in-process metrics (A9)
    stubs.py          Stub emit helpers for B/C parallel development (A2)
    providers/_errors.py   Frozen error-type contract (A2; B may extend)
    providers/stub.py      M1 stub provider (fixed text, A2)
"""

__version__ = "1.0.0-A"

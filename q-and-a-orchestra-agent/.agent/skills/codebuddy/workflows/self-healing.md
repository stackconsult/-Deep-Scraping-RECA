---
description: CodeBuddy Self-Healing Loop for autonomous error correction.
---

# CodeBuddy Self-Healing Loop

This workflow defines the procedure for autonomously correcting errors during command execution or testing.

## Workflow

1.  **Execute Command**: Run the command or test suite.
    ```bash
    # Example
    pytest tests/my_test.py
    ```

2.  **Check Status**:
    - If **SUCCESS**: Exit workflow.
    - If **FAILURE**: Proceed to step 3.

3.  **Analyze Error**:
    - Read the terminal output.
    - Identify the specific error message, file, and line number.
    - Determine the root cause (e.g., SyntaxError, ImportError, AssertionFailure).

4.  **Formulate Fix**:
    - Consult the `Debugger` persona guidelines if needed.
    - Propose a minimal code change to resolve the issue.

5.  **Apply Fix**:
    - Use `replace_file_content` or `multi_replace_file_content` to apply the fix.

6.  **Verify**:
    - Re-run the command from Step 1.
    - If it fails again, repeat from Step 3 (up to 3 times).
    - If it succeeds, document the fix and exit.

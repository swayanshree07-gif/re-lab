# 02-stack-strings: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

`strings` finds nothing useful, so the password must be built at runtime.

</details>

<details><summary>Level 2: Direction</summary>

Look for a run of `movb $imm, -0xNN(%rbp)` instructions before the compare loop.

</details>

<details><summary>Level 3: Near-spoiler</summary>

Collect those immediates in stack-offset order (not instruction order), or break after they're written and `x/s` the buffer.

</details>


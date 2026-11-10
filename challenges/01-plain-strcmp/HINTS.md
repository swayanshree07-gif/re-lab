# 01-plain-strcmp: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

What does `strings` show you? Not every string is the answer.

</details>

<details><summary>Level 2: Direction</summary>

Find the `strcmp` call and see which address goes in `%rsi`.

</details>

<details><summary>Level 3: Near-spoiler</summary>

Break on `strcmp` in gdb and read both arguments with `x/s $rdi` and `x/s $rsi`.

</details>


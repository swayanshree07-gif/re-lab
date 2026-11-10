# 03-xor-single: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

There's a blob in `.rodata` that doesn't look like text.

</details>

<details><summary>Level 2: Direction</summary>

Each byte is combined with the same single constant before the compare.

</details>

<details><summary>Level 3: Near-spoiler</summary>

Find the `xor $imm` in the loop and XOR the whole blob with it. Or try all 256 keys and look for printable text.

</details>


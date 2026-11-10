# 09-custom-hash: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

The hash looks one-way. Is each step actually invertible?

</details>

<details><summary>Level 2: Direction</summary>

Each round is a bijection (xor-shift, odd multiply, add), but the input space is too large to brute force directly.

</details>

<details><summary>Level 3: Near-spoiler</summary>

Split the input in half and meet in the middle: hash forward from one half, invert backward from the target, then match in a dict.

</details>


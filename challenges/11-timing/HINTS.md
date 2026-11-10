# 11-timing: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

Single-stepping makes it fail. Why would speed matter?

</details>

<details><summary>Level 2: Direction</summary>

Look for `rdtsc` and `clock_gettime` around the check.

</details>

<details><summary>Level 3: Near-spoiler</summary>

Compare the measured delta with the threshold and force the branch, or don't stop between the two time reads.

</details>


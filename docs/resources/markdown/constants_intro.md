---
title: "Efficient rhythms documentation: constants"
---
<!-- Uses pandoc markdown -->

When specifying pitch materials like chords, scales, and intervals, as well as when specifying general-midi instruments, the constants defined in `efficient_rhythms/er_constants.py` can be used. For ease of reference, these constants are also listed below.

In settings files, these constants can be indicated in either of the following ways:

1. As Python identifiers, e.g., `C * MAJOR_SCALE`
2. As strings, e.g., `"C * MAJOR_SCALE"`

The only advantage of using strings is that you can use the `#` character to indicate sharps. So `"C# * MAJOR_SCALE"` or `"C## * MAJOR_SCALE"` will work as expected, but `C# * MAJOR_SCALE` won't work because `#` is not a legal character in Python identifiers. (Everything after `#` will be understood as a comment.)

TODO document just and tempered pitch constants.

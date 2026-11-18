# Immutable policy snapshot preparation

This directory prepares separate copies of the existing software-assurance and
post-merge evidence policies for future exact-commit use. Their presence alone
does not activate a workflow, qualify a release, authorize a history change, or
change the current canonical source. Consumers continue to use their existing
pinned policy until a separately reviewed and tested transition is completed.

The governance snapshots originate from Core revisions `3d7d24a84b3aaacb8f2fb229e09c33da85e0545d` and `631f0b893a537807dfc59a6e69e413703a2eebdd`.
The evidence snapshots originate from Core revisions `ebbb35f038a7a3c7d46c12660968bcd50eb67580` and `4877403ba6fc69881439e70d3048da13ecb5576b`.
The evidence validators add optional expected-source validation: older records
without the new field remain supported; extended records require an independent
trusted expected identity. Existing qualification and genesis rules are not
weakened. Snapshot source and license remain under the included MIT license.

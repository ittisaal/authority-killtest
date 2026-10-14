# Controlled U/S/N benchmark

This directory separates two questions that should not be conflated.

- **U / S** are semantic outcomes for a fully specified controlled system.
- **N** is an analyzer evidence state: the supplied observation is insufficient to establish either U or S.

The suite contains nine cases:

- `SYN-U1` mirrors controlled live case U3: an editable policy selector reaches a protection-changing state.
- `SYN-U2` mirrors controlled live case U4: an editable repository property changes whether an organization rule applies.
- `SYN-U3` is a synthetic composed case where one editable value reaches two consumers.
- `SYN-S1` mirrors S2: a fixed independent floor remains.
- `SYN-S2` mirrors S3: the editable value domain has no protection-reducing state.
- `SYN-S3` confirms that editable metadata with no policy edge is not enough by itself.
- `SYN-S4` checks marginal semantics: an alternate path to a capability already present initially is S.
- `SYN-N1` hides write-authority evidence from a known-U system and must return N.
- `SYN-N2` hides the independent-floor evidence from a known-S system and must return N.

The two N cases therefore still carry a known semantic truth internally. They test conservative abstention under incomplete evidence; they are not a third kind of underlying system.

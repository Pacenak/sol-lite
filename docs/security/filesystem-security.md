# Filesystem Security

Filesystem tools resolve paths against the session workspace and use real-path containment checks.

A path outside the approved workspace is rejected even when it is presented by the model as a relative path.

"""ProofTask bundle builder package (docs/03, docs/08 B4).

Builds the immutable, self-contained bundle (ProofTask + ContextPack + DocsPack)
a ProofWorker reads. Rebuilds mint a new -rN revision rather than overwriting.
"""

from __future__ import annotations

from . import builder

__all__ = ["builder"]

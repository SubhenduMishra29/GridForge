from __future__ import annotations
class NetworkState:
    def __init__(self):
        self.topology_revision=0; self.topology_dirty=True; self._topology_valid=False
    def invalidate_topology(self):
        self.topology_revision+=1; self.topology_dirty=True; self._topology_valid=False
    def topology_rebuilt(self,*,valid:bool=True):
        if not valid:self.topology_dirty=True;self._topology_valid=False;return
        self.topology_dirty=False;self._topology_valid=True
    @property
    def topology_valid(self): return self._topology_valid and not self.topology_dirty
    def __repr__(self): return f"NetworkState(topology_revision={self.topology_revision}, topology_dirty={self.topology_dirty}, topology_valid={self.topology_valid})"
__all__=["NetworkState"]
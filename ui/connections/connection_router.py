# ============================================================
# GridForge V2 — renderer-neutral orthogonal connection router
# Author: Subhendu Mishra
# ============================================================
"""Deterministic scene-space orthogonal routing; no electrical authority."""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from math import isfinite
from numbers import Real
from typing import Iterable, TypeAlias

Point: TypeAlias = tuple[float, float]
Bounds: TypeAlias = tuple[float, float, float, float]


def _point(value: object, name: str) -> Point:
    if isinstance(value, (str, bytes)) or not isinstance(value, (tuple, list)):
        raise TypeError(f"{name} must be a two-coordinate tuple or list.")
    if len(value) != 2:
        raise ValueError(f"{name} must contain exactly two coordinates.")
    x, y = value
    if isinstance(x, bool) or not isinstance(x, Real) or isinstance(y, bool) or not isinstance(y, Real):
        raise TypeError(f"{name} coordinates must be real numbers.")
    result = float(x), float(y)
    if not all(isfinite(v) for v in result):
        raise ValueError(f"{name} coordinates must be finite.")
    return result


def _bounds(value: object, name: str) -> Bounds:
    if isinstance(value, (str, bytes)) or not isinstance(value, (tuple, list)) or len(value) != 4:
        raise TypeError(f"{name} must be (left, top, right, bottom).")
    vals = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, Real) or not isfinite(float(item)):
            raise ValueError(f"{name} coordinates must be finite real numbers.")
        vals.append(float(item))
    left, top, right, bottom = vals
    if right < left or bottom < top:
        raise ValueError(f"{name} has inverted bounds.")
    return left, top, right, bottom


@dataclass(frozen=True)
class ConnectionPath:
    """Immutable orthogonal route made of scene-space points."""

    points: tuple[Point, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.points, tuple) or len(self.points) < 2:
            raise ValueError("points must be a tuple containing at least two points.")
        pts = tuple(_point(p, f"points[{i}]") for i, p in enumerate(self.points))
        if any(a == b for a, b in zip(pts, pts[1:])):
            raise ValueError("Connection paths cannot contain zero-length segments.")
        if any(a[0] != b[0] and a[1] != b[1] for a, b in zip(pts, pts[1:])):
            raise ValueError("ConnectionPath segments must be horizontal or vertical.")
        object.__setattr__(self, "points", pts)

    @property
    def start(self) -> Point:
        return self.points[0]

    @property
    def end(self) -> Point:
        return self.points[-1]


def _inside(p: Point, r: Bounds) -> bool:
    return r[0] < p[0] < r[2] and r[1] < p[1] < r[3]


def _blocked(a: Point, b: Point, r: Bounds) -> bool:
    left, top, right, bottom = r
    if a[1] == b[1]:
        lo, hi = sorted((a[0], b[0]))
        return top < a[1] < bottom and max(lo, left) < min(hi, right)
    lo, hi = sorted((a[1], b[1]))
    return left < a[0] < right and max(lo, top) < min(hi, bottom)


def _crosses(a: Point, b: Point, c: Point, d: Point) -> bool:
    if a[1] == b[1] and c[1] == d[1]:
        return a[1] == c[1] and max(min(a[0], b[0]), min(c[0], d[0])) < min(max(a[0], b[0]), max(c[0], d[0]))
    if a[0] == b[0] and c[0] == d[0]:
        return a[0] == c[0] and max(min(a[1], b[1]), min(c[1], d[1])) < min(max(a[1], b[1]), max(c[1], d[1]))
    h1, v1 = (a, b) if a[1] == b[1] else (b, a)
    h2, v2 = (c, d) if c[1] == d[1] else (d, c)
    x, y = v1[0], h1[1]
    return min(h2[0], v2[0]) <= x <= max(h2[0], v2[0]) and min(v2[1], h2[1]) <= y <= max(v2[1], h2[1])


def _simplify(points: list[Point]) -> tuple[Point, ...]:
    result: list[Point] = []
    for p in points:
        if result and result[-1] == p:
            continue
        while len(result) >= 2:
            a, b = result[-2], result[-1]
            if (a[0] == b[0] == p[0]) or (a[1] == b[1] == p[1]):
                result.pop()
            else:
                break
        result.append(p)
    return tuple(result)


class ConnectionRouter:
    """Route around axis-aligned obstacles using a rectilinear visibility grid.

    obstacles are scene-space (left, top, right, bottom) bounds. Existing
    routes may be ConnectionPath objects or iterables of scene-space points.
    Omit the endpoint-owning equipment from obstacles, or supply terminal
    anchors outside its clearance bounds. Route geometry never establishes
    electrical connectivity. A blocked route raises ValueError rather than
    silently drawing through an obstacle.
    """

    def route(
        self,
        source_position: Point,
        target_position: Point,
        *,
        obstacles: Iterable[Bounds] = (),
        existing_routes: Iterable[ConnectionPath | Iterable[Point]] = (),
        clearance: float = 8.0,
        bend_penalty: float = 12.0,
        crossing_penalty: float = 24.0,
    ) -> ConnectionPath:
        source = _point(source_position, "source_position")
        target = _point(target_position, "target_position")
        for value, name in ((clearance, "clearance"), (bend_penalty, "bend_penalty"), (crossing_penalty, "crossing_penalty")):
            if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(float(value)) or value < 0:
                raise ValueError(f"{name} must be a finite non-negative number.")
        if source == target:
            raise ValueError("Source and target positions must be distinct.")

        rects = []
        for i, raw in enumerate(obstacles):
            l, t, r, b = _bounds(raw, f"obstacles[{i}]")
            rects.append((l - clearance, t - clearance, r + clearance, b + clearance))
        routes = []
        for i, raw in enumerate(existing_routes):
            raw_points = raw.points if isinstance(raw, ConnectionPath) else tuple(raw)
            pts = tuple(_point(p, f"existing_routes[{i}]") for p in raw_points)
            if len(pts) >= 2:
                routes.append(pts)
        if any(_inside(p, r) for p in (source, target) for r in rects):
            raise ValueError("An endpoint lies inside an obstacle clearance region.")

        xs, ys = {source[0], target[0]}, {source[1], target[1]}
        for l, t, r, b in rects:
            xs.update((l, r))
            ys.update((t, b))
        nodes = [(x, y) for y in sorted(ys) for x in sorted(xs) if not any(_inside((x, y), r) for r in rects)]
        index = {p: i for i, p in enumerate(nodes)}
        if source not in index or target not in index:
            raise ValueError("No route is available for the supplied endpoints.")
        adjacency: list[list[tuple[int, float, int]]] = [[] for _ in nodes]
        rows: dict[float, list[Point]] = {}
        cols: dict[float, list[Point]] = {}
        for p in nodes:
            rows.setdefault(p[1], []).append(p)
            cols.setdefault(p[0], []).append(p)

        def connect(a: Point, b: Point) -> None:
            if any(_blocked(a, b, rect) for rect in rects):
                return
            penalty = 0.0
            for route in routes:
                if any(_crosses(a, b, c, d) for c, d in zip(route, route[1:])):
                    penalty += crossing_penalty
            direction = 0 if a[1] == b[1] else 1
            distance = abs(a[0] - b[0]) + abs(a[1] - b[1]) + penalty
            ia, ib = index[a], index[b]
            adjacency[ia].append((ib, distance, direction))
            adjacency[ib].append((ia, distance, direction))

        for row in rows.values():
            row.sort()
            for a, b in zip(row, row[1:]):
                connect(a, b)
        for col in cols.values():
            col.sort(key=lambda p: p[1])
            for a, b in zip(col, col[1:]):
                connect(a, b)

        start = (index[source], -1)
        distances = {start: 0.0}
        previous: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
        queue = []
        serial = count()
        heappush(queue, (0.0, next(serial), start))
        goal = None
        while queue:
            cost, _, state = heappop(queue)
            if cost != distances.get(state):
                continue
            node, prior_direction = state
            if node == index[target]:
                goal = state
                break
            for neighbor, edge_cost, direction in adjacency[node]:
                bend = float(bend_penalty) if prior_direction not in (-1, direction) else 0.0
                nxt = (neighbor, direction)
                new_cost = cost + edge_cost + bend
                if new_cost < distances.get(nxt, float("inf")):
                    distances[nxt] = new_cost
                    previous[nxt] = state
                    heappush(queue, (new_cost, next(serial), nxt))
        if goal is None:
            raise ValueError("No orthogonal route exists around the supplied obstacles.")
        path = []
        cursor = goal
        while cursor is not None:
            path.append(nodes[cursor[0]])
            cursor = previous[cursor]
        path.reverse()
        return ConnectionPath(_simplify(path))


__all__ = ["Bounds", "ConnectionPath", "ConnectionRouter", "Point"]

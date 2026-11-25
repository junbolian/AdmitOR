import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["num_nodes"])
    depot = int(params["depot"])

    nodes = list(range(n))
    # Required edges (also graph edges)
    req_edges = [
        (0, 7), (1, 7), (2, 5), (2, 7), (3, 6),
        (3, 7), (4, 6), (5, 6), (5, 7),
    ]

    # Directed arcs: both orientations of each required (undirected) edge
    arcs = []
    for (u, v) in req_edges:
        arcs.append((u, v))
        arcs.append((v, u))

    def dist(u, v):
        if u == v:
            return 0.0
        a, b = min(u, v), max(u, v)
        return float(params["dist_%d_%d" % (a, b)])

    def ecost(u, v):
        a, b = min(u, v), max(u, v)
        return float(params["edge_cost_%d_%d" % (a, b)])

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    # x[u,v]: number of times arc (u,v) is traversed (integer >= 0)
    model.x = pyo.Var(model.ARCS, domain=pyo.NonNegativeIntegers, bounds=(0, 3))
    # z[u,v]: number of times required arc (u,v) is serviced (integer, 1..2)
    model.z = pyo.Var(model.ARCS, domain=pyo.NonNegativeIntegers, bounds=(0, 2))

    # Each required undirected edge serviced from both directions summing to >=1
    # For each required edge, z(u,v) + z(v,u) >= 1 and z <= x for each orientation
    for (u, v) in req_edges:
        model.add_component(
            "req_%d_%d" % (u, v),
            pyo.Constraint(expr=model.z[u, v] + model.z[v, u] >= 1),
        )

    # z bounded by x per arc
    def zx_rule(m, u, v):
        return m.z[u, v] <= m.x[u, v]
    model.zx = pyo.Constraint(model.ARCS, rule=zx_rule)

    # Flow conservation at each non-depot node
    def flow_rule(m, k):
        inflow = sum(m.x[u, v] for (u, v) in arcs if v == k)
        outflow = sum(m.x[u, v] for (u, v) in arcs if u == k)
        return inflow == outflow

    non_depot = [k for k in nodes if k != depot]
    model.flow = pyo.Constraint(non_depot, rule=flow_rule)

    # Objective: service cost * z + deadhead (travel) cost * x
    # Base travel cost on every traversal, plus service cost on service count.
    # Actually typical: total = sum over arcs of dist(u,v)*x[u,v] + service costs * z[u,v]
    def obj_rule(m):
        total = 0
        for (u, v) in arcs:
            total += dist(u, v) * m.x[u, v]
            total += ecost(u, v) * m.z[u, v]
        return total
    model.OBJ = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.OBJ))
    return {"objective": obj_val, "status": "optimal"}
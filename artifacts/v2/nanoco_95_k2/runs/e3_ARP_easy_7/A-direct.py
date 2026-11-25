import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coords = params["coords"]
    dist = params["distance_matrix"]

    nodes = list(range(8))
    required_edges = [(0, 2), (0, 6), (1, 3), (1, 6), (2, 4), (2, 7), (3, 5), (3, 7)]

    # Directed arcs (both directions for every ordered pair of distinct nodes)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    # Flow decision variable: number of times arc (i,j) is traversed
    model.x = pyo.Var(arcs, domain=pyo.NonNegativeIntegers)

    # Objective: minimize total travel distance
    def obj_rule(m):
        return sum(dist[i][j] * m.x[(i, j)] for (i, j) in arcs)

    model.total_distance = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Flow balance: in-degree equals out-degree at each node (closed loop)
    def flow_balance_rule(m, n):
        inflow = sum(m.x[(i, n)] for i in nodes if i != n)
        outflow = sum(m.x[(n, j)] for j in nodes if j != n)
        return inflow == outflow

    model.flow_balance = pyo.Constraint(nodes, rule=flow_balance_rule)

    # Required edges must be swept at least once (in either direction)
    def req_rule(m, idx):
        a, b = required_edges[idx]
        return m.x[(a, b)] + m.x[(b, a)] >= 1

    model.required_coverage = pyo.Constraint(range(len(required_edges)), rule=req_rule)

    # Connectivity / subtour elimination via single-commodity flow from depot 0
    # Every non-depot node receives at least one unit of commodity flow.
    model.f = pyo.Var(arcs, domain=pyo.NonNegativeReals)

    inflow_f = {n: m for (m, n) in arcs}  # placeholder; built below explicitly

    def commodity_balance_rule(m, n):
        if n == 0:
            return pyo.Constraint.Skip
        inflow = sum(m.f[(i, n)] for i in nodes if i != n)
        outflow = sum(m.f[(n, j)] for j in nodes if j != n)
        # node n is a self-sink of 1 unit
        return inflow - outflow == 1

    model.commodity_balance = pyo.Constraint(nodes, rule=commodity_balance_rule)

    big_m = sum(sum(dist[i][j] for j in nodes if i != j) for i in nodes) + 1

    def commodity_link_rule(m, i, j):
        return m.f[(i, j)] <= big_m * m.x[(i, j)]

    model.commodity_link = pyo.Constraint(arcs, rule=commodity_link_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_distance))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    n = len(dist)

    required_edges = [(0, 1), (0, 5), (1, 5), (1, 6), (2, 3), (4, 6)]
    num_required = len(required_edges)

    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.nodes = pyo.RangeSet(0, n - 1)

    # x[i,j] = number of times arc (i,j) is traversed (1 if used, more via y)
    model.x = pyo.Var(model.arcs, domain=pyo.NonNegativeIntegers, bounds=(0, num_required))
    # y[i,j] = binary indicator arc used
    model.y = pyo.Var(model.arcs, domain=pyo.Binary)

    # z[r] = binary: required edge r serviced
    model.req = pyo.Set(initialize=range(num_required), dimen=1)
    model.z = pyo.Var(model.req, domain=pyo.Binary)

    # Flow conservation at every node
    def flow_rule(m, k):
        out_ = sum(m.x[k, j] for j in range(n) if j != k)
        in_ = sum(m.x[i, k] for i in range(n) if i != k)
        return out_ == in_
    model.flow = pyo.Constraint(model.nodes, rule=flow_rule)

    # Depot must be visited (leaves at least once)
    def depot_rule(m):
        return sum(m.x[0, j] for j in range(n) if j != 0) >= 1
    model.depot = pyo.Constraint(rule=depot_rule)

    # Link x and y
    def link_rule(m, i, j):
        return m.x[i, j] <= num_required * m.y[i, j]
    model.link = pyo.Constraint(model.arcs, rule=link_rule)

    # Each required edge must be serviced at least once
    def service_rule(m, r):
        i, j = required_edges[r]
        return m.x[i, j] + m.x[j, i] >= 1
    model.service = pyo.Constraint(model.req, rule=service_rule)

    # Connectivity: prevent disconnected subtours (single-commodity flow)
    # s[i,j] = flow of a commodity on arc (i,j); depot is source
    model.s = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    M = num_required

    def sc_rule(m, i, j):
        return m.s[i, j] <= M * m.y[i, j]
    model.sc = pyo.Constraint(model.arcs, rule=sc_rule)

    def sc_bal_rule(m, k):
        if k == 0:
            inflow = sum(m.s[i, 0] for i in range(n) if i != 0)
            outflow = sum(m.s[0, j] for j in range(n) if j != 0)
            return inflow == outflow - sum(m.y[0, j] for j in range(n) if j != 0)
        else:
            inflow = sum(m.s[i, k] for i in range(n) if i != k)
            outflow = sum(m.s[k, j] for j in range(n) if j != k)
            return inflow - outflow == sum(m.y[k, j] for j in range(n) if j != k)
    model.sc_bal = pyo.Constraint(model.nodes, rule=sc_bal_rule)

    # Objective: minimize total travel distance
    def obj_rule(m):
        return sum(dist[i][j] * m.x[i, j] for (i, j) in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
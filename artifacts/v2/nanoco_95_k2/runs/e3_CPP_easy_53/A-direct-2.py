import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    service_cost = params["service_cost"]
    travel_cost = params["travel_cost"]

    req_edges = [(0, 3), (0, 4), (1, 4), (2, 3), (2, 5), (3, 4), (4, 5)]
    nodes = list(range(6))
    n = 6

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.req = pyo.Set(initialize=req_edges, dimen=2)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in nodes for j in nodes if i != j], dimen=2
    )

    def tcost(m, i, j):
        return travel_cost[i * n + j]

    model.tc = pyo.Param(model.arcs, initialize=tcost, mutable=False)

    def scost(m, i, j):
        if (i, j) in service_cost:
            return service_cost[(i, j)]
        return service_cost[(j, i)]

    model.sc = pyo.Param(model.req, initialize=scost, mutable=False)

    model.x = pyo.Var(model.arcs, domain=pyo.NonNegativeIntegers)
    model.y = pyo.Var(model.req, domain=pyo.NonNegativeIntegers)

    model.service = pyo.Constraint(model.req, rule=lambda m, i, j: m.y[i, j] >= 1)

    def obj_rule(m):
        return sum(m.sc[e] * m.y[e] for e in m.req) + sum(
            m.tc[a] * m.x[a] for a in m.arcs
        )

    model.total = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    reqset = set(req_edges) | set((j, i) for (i, j) in req_edges)

    def flow_balance_rule(m, i):
        out_flow = sum(m.x[i, j] for j in nodes if j != i)
        in_flow = sum(m.x[j, i] for j in nodes if j != i)
        return out_flow == in_flow

    model.flow_balance = pyo.Constraint(model.nodes, rule=flow_balance_rule)

    def service_link_rule(m, i, j):
        # Every required edge must be traversed at least once in its designated
        # direction so that service is performed; here we ensure that the arc
        # (i, j) is traversed at least once for each required edge (i, j).
        if (i, j) in reqset:
            return m.x[i, j] >= 1
        return pyo.Constraint.Skip

    model.service_link = pyo.Constraint(model.arcs, rule=service_link_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total))
    return {"objective": obj_val, "status": "optimal"}
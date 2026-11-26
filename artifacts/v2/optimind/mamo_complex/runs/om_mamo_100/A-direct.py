import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_matrix = params["capacity_matrix"]
    n = len(capacity_matrix)
    source = 0
    sink = n - 1

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, n - 1)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in range(n) for j in range(n)
                    if i != j and capacity_matrix[i][j] > 0],
        dimen=2,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def arc_cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= capacity_matrix[i][j]

    model.arc_cap = pyo.Constraint(model.arcs, rule=arc_cap_rule)

    def conservation_rule(mdl, k):
        inflow = sum(mdl.flow[i, k] for (i, kk) in mdl.arcs if kk == k)
        outflow = sum(mdl.flow[k, j] for (kk, j) in mdl.arcs if kk == k)
        if k == source:
            return outflow - inflow >= 0
        if k == sink:
            return inflow - outflow >= 0
        return inflow - outflow == 0

    model.conservation = pyo.Constraint(model.nodes, rule=conservation_rule)

    def obj_rule(mdl):
        return sum(mdl.flow[source, j] for (i, j) in mdl.arcs if i == source) \
            - sum(mdl.flow[i, source] for (i, j) in mdl.arcs if j == source)

    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_flow))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": str(exc)[:200]}
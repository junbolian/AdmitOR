import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    caps = params["line_capacities"]
    n = 8
    source = 0
    sink = 7

    model = pyo.ConcreteModel()

    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]

    model.A = pyo.Set(initialize=arcs, dimen=2)

    def cap_init(mdl, i, j):
        val = caps[i][j] if isinstance(caps, (list, tuple)) else caps.get(i, {}).get(j, 0) if hasattr(caps, "get") else caps[(i, j)] if (i, j) in caps else 0
        return float(val)

    model.cap = pyo.Param(model.A, initialize=cap_init, within=pyo.NonNegativeReals)

    model.flow = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def flow_ub(mdl, i, j):
        return mdl.flow[i, j] <= mdl.cap[i, j]

    model.cap_con = pyo.Constraint(model.A, rule=flow_ub)

    def balance_rule(mdl, k):
        inflow = sum(mdl.flow[i, k] for i in range(n) if i != k)
        outflow = sum(mdl.flow[k, j] for j in range(n) if j != k)
        if k == source:
            return outflow - inflow <= 0
        elif k == sink:
            return inflow - outflow <= 0
        return inflow - outflow == 0

    model.balance = pyo.Constraint(range(n), rule=balance_rule)

    def obj_rule(mdl):
        return sum(mdl.flow[source, j] for j in range(n) if j != source)

    model.total = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or unsolved"}
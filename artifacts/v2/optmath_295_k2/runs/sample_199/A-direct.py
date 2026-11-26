import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = int(params["num_cities"])
    supply_demand = params["supply_demand"]
    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    arcs = [(i, j) for i in range(num_cities) for j in range(num_cities) if i != j]

    # cost_matrix / capacity_matrix may be given either as flat row-major lists
    # (skipping diagonal) or normalized by the harness into per-arc mappings.
    def _lookup(data, k, a):
        if isinstance(data, dict):
            if a in data:
                return data[a]
            return data[list(data.keys())[k]]
        if isinstance(data, (list, tuple)):
            return data[k]
        # assume mapping-like with tuple keys
        if a in data:
            return data[a]
        if (a[0], a[1]) in data:
            return data[(a[0], a[1])]
        return data[k]

    cost = {a: _lookup(cost_matrix, k, a) for k, a in enumerate(arcs)}
    cap = {a: _lookup(capacity_matrix, k, a) for k, a in enumerate(arcs)}

    # Build capacities robustly: guard against missing arcs by defaulting to 0.
    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arcs, within=pyo.NonNegativeReals)

    def cap_rule(md, i, j):
        return md.flow[i, j] <= cap[(i, j)]
    model.cap_con = pyo.Constraint(model.arcs, rule=cap_rule)

    def balance_rule(md, k):
        inflow = sum(md.flow[i, k] for i in range(num_cities) if i != k)
        outflow = sum(md.flow[k, j] for j in range(num_cities) if j != k)
        return inflow - outflow == supply_demand[k]
    model.balance_con = pyo.Constraint(range(num_cities), rule=balance_rule)

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.flow[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except Exception:
        return {"objective": None, "status": "solver error"}

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or unsolvable"}

    return {"objective": obj_val, "status": "optimal"}
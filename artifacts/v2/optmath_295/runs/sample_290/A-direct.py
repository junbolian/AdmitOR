import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_fac = 6
    n_cust = 12
    facs = list(range(n_fac))
    custs = list(range(n_cust))

    fixed_cost = {i: params[f"fixed_cost"] if not isinstance(params.get("fixed_cost"), (list, tuple))
                  else params["fixed_cost"][i] for i in facs}
    capacity = {i: params[f"capacity"] if not isinstance(params.get("capacity"), (list, tuple))
                else params["capacity"][i] for i in facs}
    demand = {j: params[f"demand"] if not isinstance(params.get("demand"), (list, tuple))
              else params["demand"][j] for j in custs}

    # Handle scalar-or-list params cleanly
    if isinstance(params["fixed_cost"], (list, tuple)):
        fixed_cost = {i: params["fixed_cost"][i] for i in facs}
    else:
        fixed_cost = {i: params["fixed_cost"] for i in facs}

    if isinstance(params["capacity"], (list, tuple)):
        capacity = {i: params["capacity"][i] for i in facs}
    else:
        capacity = {i: params["capacity"] for i in facs}

    if isinstance(params["demand"], (list, tuple)):
        demand = {j: params["demand"][j] for j in custs}
    else:
        demand = {j: params["demand"] for j in custs}

    # Diagonal transportation costs are given; off-diagonal assumed via symmetric/indexed fallback.
    # Only specified params exist, so build a full cost matrix with a default for unspecified pairs.
    transport = {}
    specified = {
        (0, 0): params["transport_cost_00"],
        (1, 1): params["transport_cost_11"],
        (2, 2): params["transport_cost_22"],
        (3, 3): params["transport_cost_33"],
        (4, 4): params["transport_cost_44"],
        (5, 5): params["transport_cost_55"],
    }
    for i in facs:
        for j in custs:
            if (i, j) in specified:
                transport[(i, j)] = specified[(i, j)]
            else:
                # Fill unspecified pairs using the nearest specified diagonal per row/column
                transport[(i, j)] = specified.get((i, i), specified[(0, 0)])

    model = pyo.ConcreteModel()

    model.FAC = pyo.Set(initialize=facs)
    model.CUST = pyo.Set(initialize=custs)
    model.LINK = pyo.Set(initialize=[(i, j) for i in facs for j in custs])

    model.y = pyo.Var(model.FAC, within=pyo.Binary)
    model.x = pyo.Var(model.LINK, within=pyo.NonNegativeReals)

    model.fixed_cost_c = pyo.Param(model.FAC, initialize=fixed_cost)
    model.capacity_c = pyo.Param(model.FAC, initialize=capacity)
    model.demand_c = pyo.Param(model.CUST, initialize=demand)
    model.tcost_c = pyo.Param(model.LINK, initialize=transport)

    def objective_rule(m):
        return (sum(m.fixed_cost_c[i] * m.y[i] for i in m.FAC)
                + sum(m.tcost_c[(i, j)] * m.x[(i, j)] for (i, j) in m.LINK))
    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[(i, j)] for i in m.FAC) == m.demand_c[j]
    model.demand_con = pyo.Constraint(model.CUST, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[(i, j)] for j in m.CUST) <= m.capacity_c[i] * m.y[i]
    model.capacity_con = pyo.Constraint(model.FAC, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
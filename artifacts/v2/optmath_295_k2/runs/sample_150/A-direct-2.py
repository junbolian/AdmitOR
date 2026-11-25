import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = 6
    arcs = [(i, j) for i in range(N) for j in range(N) if i != j]

    # Extract net supply/demand vector
    b = {i: float(params["supply_demand"][i]) for i in range(N)}

    # Extract per-arc parameters
    f = {(i, j): float(params[f"fixed_cost_{i}_{j}"]) for (i, j) in arcs}
    c = {(i, j): float(params[f"variable_cost_{i}_{j}"]) for (i, j) in arcs}
    u = {(i, j): float(params[f"capacity_{i}_{j}"]) for (i, j) in arcs}

    # Total demand magnitude -> a safe big-M per arc (use arc capacity as tight M)
    # Flow on arc is already bounded by u, and y * u bounds x, so M_ij = u_ij works.
    M = {(i, j): u[(i, j)] for (i, j) in arcs}

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.NODES = pyo.Set(initialize=range(N))

    model.x = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.ARCS, domain=pyo.Binary)

    # Linking: flow <= capacity * binary
    def cap_rule(m, i, j):
        return m.x[(i, j)] <= M[(i, j)] * m.y[(i, j)]

    model.cap_link = pyo.Constraint(model.ARCS, rule=cap_rule)

    # Flow balance: net outflow - net inflow = supply
    # (supply positive => net producer; demand negative => net consumer)
    def balance_rule(m, i):
        out_flow = sum(m.x[(i, j)] for j in range(N) if j != i)
        in_flow = sum(m.x[(j, i)] for j in range(N) if j != i)
        return out_flow - in_flow == b[i]

    model.balance = pyo.Constraint(model.NODES, rule=balance_rule)

    # Objective
    def obj_rule(m):
        fixed = sum(f[(i, j)] * m.y[(i, j)] for (i, j) in arcs)
        var = sum(c[(i, j)] * m.x[(i, j)] for (i, j) in arcs)
        return fixed + var

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [0, 1, 2, 3, 4, 5]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    # Supplies (positive) and demands (positive needed)
    supply = {
        0: params["supply_0"],
        1: params["supply_1"],
    }
    demand = {
        2: params["demand_2"],
        3: params["demand_3"],
        4: params["demand_4"],
        5: params["demand_5"],
    }

    # Net b: positive = supply available, negative = demand required
    b = {c: 0.0 for c in cities}
    for c, v in supply.items():
        b[c] += v
    for c, v in demand.items():
        b[c] -= v

    cost = {(i, j): params["cost_%d_to_%d" % (i, j)] for (i, j) in arcs}
    cap = {(i, j): params["cap_%d_to_%d" % (i, j)] for (i, j) in arcs}

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals, bounds=lambda m, i, j: (0, cap[(i, j)]))

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[i, j] for (i, j) in m.ARCS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, c):
        outflow = sum(m.x[c, j] for j in cities if j != c)
        inflow = sum(m.x[i, c] for i in cities if i != c)
        return outflow - inflow == b[c]

    model.balance = pyo.Constraint(cities, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
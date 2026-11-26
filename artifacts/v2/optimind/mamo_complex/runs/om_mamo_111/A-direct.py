import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    regions = [1, 2, 3, 4, 5]
    arcs = [(1, 2), (1, 3), (1, 4), (1, 5),
            (2, 3), (2, 4), (2, 5),
            (3, 4), (3, 5),
            (4, 5)]

    cost = {
        (1, 2): params["cost_12"],
        (1, 3): params["cost_13"],
        (1, 4): params["cost_14"],
        (1, 5): params["cost_15"],
        (2, 3): params["cost_23"],
        (2, 4): params["cost_24"],
        (2, 5): params["cost_25"],
        (3, 4): params["cost_34"],
        (3, 5): params["cost_35"],
        (4, 5): params["cost_45"],
    }

    supply = {r: params["supply_%d" % r] for r in regions}
    demand = {r: params["demand_%d" % r] for r in regions}

    model = pyo.ConcreteModel()

    model.flow = pyo.Var(arcs, domain=pyo.NonNegativeReals)

    model.total_cost = pyo.Objective(
        expr=sum(cost[a] * model.flow[a] for a in arcs),
        sense=pyo.minimize,
    )

    def balance_rule(m, r):
        inflow = sum(m.flow[(i, j)] for (i, j) in arcs if j == r)
        outflow = sum(m.flow[(i, j)] for (i, j) in arcs if i == r)
        return supply[r] + inflow - outflow == demand[r]

    model.balance = pyo.Constraint(regions, rule=balance_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}
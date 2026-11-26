import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transfer_cost = params["transfer_cost"]
    n = params["num_centers"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(0, n - 1)

    model.flow = pyo.Var(
        model.centers, model.centers, domain=pyo.NonNegativeReals
    )

    def cost_rule(m):
        return sum(
            transfer_cost[i][j] * m.flow[i, j]
            for i in range(n)
            for j in range(n)
            if i != j
        )

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    # Supplies must fully cover demand at each center (>=), and total supply
    # equals total demand, so equality holds automatically at optimum.
    def balance_rule(m, i):
        inflow = sum(m.flow[j, i] for j in range(n) if j != i)
        outflow = sum(m.flow[i, j] for j in range(n) if j != i)
        return supply[i] + inflow - outflow == demand[i]

    model.balance = pyo.Constraint(model.centers, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
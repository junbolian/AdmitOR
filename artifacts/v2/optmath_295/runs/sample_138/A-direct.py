import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_demand = params["supply_demand"]
    costs = params["costs"]
    capacities = params["capacities"]

    n = len(supply_demand)

    model = pyo.ConcreteModel()

    # Ordered pairs (i, j), i != j, consistent with the row ordering in costs/capacities
    model.ARCS = pyo.Set(
        initialize=[(i, j) for i in range(n) for j in range(n) if j != i],
        dimen=2,
    )

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    # Map (i, j) -> position within row i of the costs/capacities arrays
    def pos(i, j):
        return j if j < i else j - 1

    # Capacity constraints
    def cap_rule(model, i, j):
        return model.flow[i, j] <= capacities[i][pos(i, j)]

    model.cap_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    # Flow balance: outflow - inflow = supply_demand[i]
    def balance_rule(model, i):
        outflow = sum(model.flow[i, j] for j in range(n) if j != i)
        inflow = sum(model.flow[j, i] for j in range(n) if j != i)
        return outflow - inflow == supply_demand[i]

    model.balance_con = pyo.Constraint(range(n), rule=balance_rule)

    # Objective
    def obj_rule(model):
        return sum(
            costs[i][pos(i, j)] * model.flow[i, j] for (i, j) in model.ARCS
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
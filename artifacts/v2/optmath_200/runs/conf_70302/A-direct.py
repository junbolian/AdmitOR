import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    contract_demand = params["contract_demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    nP = len(capacity)
    nC = len(contract_demand)
    producers = list(range(nP))
    contracts = list(range(nC))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(producers, contracts, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(producers, contracts, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[p][c] * m.x[p, c] for p in producers for c in contracts)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.capacity_con = pyo.Constraint(
        producers,
        rule=lambda m, p: sum(m.x[p, c] for c in contracts) <= capacity[p]
    )

    model.demand_con = pyo.Constraint(
        contracts,
        rule=lambda m, c: sum(m.x[p, c] for p in producers) >= contract_demand[c]
    )

    model.min_delivery_con = pyo.Constraint(
        producers, contracts,
        rule=lambda m, p, c: m.x[p, c] >= min_delivery[p] * m.y[p, c]
    )

    model.link_con = pyo.Constraint(
        producers, contracts,
        rule=lambda m, p, c: m.x[p, c] <= capacity[p] * m.y[p, c]
    )

    model.num_producers_con = pyo.Constraint(
        contracts,
        rule=lambda m, c: sum(m.y[p, c] for p in producers) >= 2
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
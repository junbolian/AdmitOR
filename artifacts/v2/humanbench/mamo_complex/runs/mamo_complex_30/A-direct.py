import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    centers = list(range(4))
    stores = list(range(6))

    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=centers)
    model.S = pyo.Set(initialize=stores)

    model.z = pyo.Var(model.C, domain=pyo.Binary)
    model.x = pyo.Var(model.C, model.S, domain=pyo.NonNegativeReals)

    def opening_rule(m):
        return sum(opening_costs[i] * m.z[i] for i in m.C)

    def transport_rule(m):
        return sum(transport_costs[i][j] * m.x[i, j] for i in m.C for j in m.S)

    model.opening_cost_expr = pyo.Expression(rule=opening_rule)
    model.transport_cost_expr = pyo.Expression(rule=transport_rule)

    model.total_cost = pyo.Objective(
        expr=model.opening_cost_expr + model.transport_cost_expr,
        sense=pyo.minimize,
    )

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.C) == demands[j]

    model.demand_constraint = pyo.Constraint(model.S, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.S) <= capacities[i] * m.z[i]

    model.capacity_constraint = pyo.Constraint(model.C, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
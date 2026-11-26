import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_supplies = params["initial_supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]

    n = 4
    cities = list(range(n))

    model = pyo.ConcreteModel()
    model.cities_from = pyo.Set(initialize=cities)
    model.cities_to = pyo.Set(initialize=cities)

    model.flow = pyo.Var(model.cities_from, model.cities_to, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            transport_costs[i][j] * m.flow[i, j]
            for i in m.cities_from
            for j in m.cities_to
            if i != j
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # final amount in each city i = initial + inflow - outflow >= demand
    def balance_rule(m, i):
        inflow = sum(m.flow[j, i] for j in m.cities_to if j != i)
        outflow = sum(m.flow[i, j] for j in m.cities_to if j != i)
        return initial_supplies[i] + inflow - outflow >= demands[i]

    model.demand_con = pyo.Constraint(model.cities_from, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
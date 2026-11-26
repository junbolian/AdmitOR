import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transportation_costs = params["transportation_costs"]
    demands = params["demands"]
    capacities = params["capacities"]
    num_centers = int(params["num_centers"])
    num_stores = int(params["num_stores"])

    def tcost(i, j):
        if isinstance(transportation_costs, dict):
            entry = transportation_costs.get((i, j), transportation_costs.get(i))
            if isinstance(entry, dict):
                return entry[j]
            if isinstance(entry, (list, tuple)):
                return entry[j]
            return entry
        return transportation_costs[i][j]

    centers = range(num_centers)
    stores = range(num_stores)

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=list(centers))
    model.J = pyo.Set(initialize=list(stores))

    model.y = pyo.Var(model.I, domain=pyo.Binary)
    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(opening_costs[i] * m.y[i] for i in m.I) + sum(
            tcost(i, j) * m.x[i, j] for i in m.I for j in m.J
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.I) == demands[j]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.J) <= capacities[i] * m.y[i]

    model.capacity_con = pyo.Constraint(model.I, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
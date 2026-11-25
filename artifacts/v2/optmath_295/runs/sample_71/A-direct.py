import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    shipping_costs = params["shipping_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    num_facilities = 6
    num_customers = 9
    facilities = range(num_facilities)
    customers = range(num_customers)

    model = pyo.ConcreteModel()

    model.facilities = pyo.Set(initialize=list(facilities))
    model.customers = pyo.Set(initialize=list(customers))

    model.open_facility = pyo.Var(model.facilities, domain=pyo.Binary)
    model.ship = pyo.Var(model.facilities, model.customers, domain=pyo.NonNegativeReals)

    def objective_rule(m):
        fixed_term = sum(fixed_costs[f] * m.open_facility[f] for f in m.facilities)
        ship_term = sum(
            shipping_costs[c][f] * m.ship[f, c]
            for f in m.facilities
            for c in m.customers
        )
        return fixed_term + ship_term

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def demand_rule(m, c):
        return sum(m.ship[f, c] for f in m.facilities) == demands[c]

    model.demand_con = pyo.Constraint(model.customers, rule=demand_rule)

    def capacity_rule(m, f):
        return sum(m.ship[f, c] for c in m.customers) <= capacities[f] * m.open_facility[f]

    model.capacity_con = pyo.Constraint(model.facilities, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
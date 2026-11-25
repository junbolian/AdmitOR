import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    shipping_costs = params["shipping_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    num_facilities = len(fixed_costs)
    num_customers = len(demands)

    facilities = range(num_facilities)
    customers = range(num_customers)

    model = pyo.ConcreteModel()

    model.facilities = pyo.Set(initialize=facilities)
    model.customers = pyo.Set(initialize=customers)

    model.open_facility = pyo.Var(model.facilities, domain=pyo.Binary)
    model.ship = pyo.Var(
        model.customers, model.facilities, domain=pyo.NonNegativeReals
    )

    def objective_rule(mdl):
        fixed = sum(
            fixed_costs[j] * mdl.open_facility[j] for j in mdl.facilities
        )
        variable = sum(
            shipping_costs[i][j] * mdl.ship[i, j]
            for i in mdl.customers
            for j in mdl.facilities
        )
        return fixed + variable

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def demand_rule(mdl, i):
        return (
            sum(mdl.ship[i, j] for j in mdl.facilities) == demands[i]
        )

    model.demand_constraint = pyo.Constraint(
        model.customers, rule=demand_rule
    )

    def capacity_rule(mdl, j):
        return (
            sum(mdl.ship[i, j] for i in mdl.customers)
            <= capacities[j] * mdl.open_facility[j]
        )

    model.capacity_constraint = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
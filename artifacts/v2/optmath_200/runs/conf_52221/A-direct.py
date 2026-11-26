import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_producers_per_contract = params["min_producers_per_contract"]
    unit_cost = params["unit_cost"]
    min_delivery_if_assigned = params["min_delivery_if_assigned"]

    num_producers = len(producer_capacity)
    num_contracts = len(contract_demand)

    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, num_producers - 1)
    model.contracts = pyo.RangeSet(0, num_contracts - 1)

    model.amount = pyo.Var(model.producers, model.contracts, domain=pyo.NonNegativeReals)
    model.assign = pyo.Var(model.producers, model.contracts, domain=pyo.Binary)

    def objective_rule(mdl):
        return sum(
            unit_cost[i][j] * mdl.amount[i, j]
            for i in mdl.producers
            for j in mdl.contracts
        )

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    model.capacity_limit = pyo.Constraint(
        model.producers,
        rule=lambda mdl, i: sum(mdl.amount[i, j] for j in mdl.contracts)
        <= producer_capacity[i],
    )

    model.demand_met = pyo.Constraint(
        model.contracts,
        rule=lambda mdl, j: sum(mdl.amount[i, j] for i in mdl.producers)
        >= contract_demand[j],
    )

    model.min_producers = pyo.Constraint(
        model.contracts,
        rule=lambda mdl, j: sum(mdl.assign[i, j] for i in mdl.producers)
        >= min_producers_per_contract[j],
    )

    model.link_upper = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=lambda mdl, i, j: mdl.amount[i, j]
        <= producer_capacity[i] * mdl.assign[i, j],
    )

    model.link_lower = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=lambda mdl, i, j: mdl.amount[i, j]
        >= min_delivery_if_assigned[i] * mdl.assign[i, j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}
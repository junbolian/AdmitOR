import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    production_cost = params["production_cost"]
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_contributors = params["min_contributors"]
    min_delivery_per_producer = params["min_delivery_per_producer"]

    num_producers = len(producer_capacity)
    num_contracts = len(contract_demand)

    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, num_producers - 1)
    model.contracts = pyo.RangeSet(0, num_contracts - 1)


    def cost_init(mdl, i, j):
        return production_cost[i][j]
    model.production_cost = pyo.Param(model.producers, model.contracts, initialize=cost_init, mutable=False)

    model.producer_capacity = pyo.Param(model.producers, initialize=lambda mdl, i: producer_capacity[i])
    model.contract_demand = pyo.Param(model.contracts, initialize=lambda mdl, j: contract_demand[j])
    model.min_contributors = pyo.Param(model.contracts, initialize=lambda mdl, j: min_contributors[j])
    model.min_delivery = pyo.Param(model.producers, initialize=lambda mdl, i: min_delivery_per_producer[i])

    model.x = pyo.Var(model.producers, model.contracts, within=pyo.NonNegativeReals)
    model.y = pyo.Var(model.producers, model.contracts, within=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(model.production_cost[i, j] * model.x[i, j] for i in model.producers for j in model.contracts),
        sense=pyo.minimize,
    )

    # Linking constraints: min delivery if contributing, and not exceed capacity-based upper bound otherwise
    model.link_lower = pyo.Constraint(
        model.producers, model.contracts,
        rule=lambda mdl, i, j: mdl.x[i, j] >= mdl.min_delivery[i] * mdl.y[i, j]
    )
    model.link_upper = pyo.Constraint(
        model.producers, model.contracts,
        rule=lambda mdl, i, j: mdl.x[i, j] <= mdl.producer_capacity[i] * mdl.y[i, j]
    )

    # Capacity constraints
    model.capacity = pyo.Constraint(
        model.producers,
        rule=lambda mdl, i: sum(mdl.x[i, j] for j in mdl.contracts) <= mdl.producer_capacity[i]
    )

    # Contract fulfillment
    model.demand = pyo.Constraint(
        model.contracts,
        rule=lambda mdl, j: sum(mdl.x[i, j] for i in mdl.producers) >= mdl.contract_demand[j]
    )

    # Minimum contributors
    model.min_contrib = pyo.Constraint(
        model.contracts,
        rule=lambda mdl, j: sum(mdl.y[i, j] for i in mdl.producers) >= mdl.min_contributors[j]
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
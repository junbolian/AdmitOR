# IR: {"sets":{"P":[0,1,2],"C":[0,1,2,3]},"params":{"capacity":"capacity[p]","demand":"demand[c]","min_delivery":"min_delivery[p]","cost":"cost[p][c]"},"variables":{"energy[p,c]":"NonNegativeReals","participates[p,c]":"Binary"},"constraints":["sum(c in C, energy[p,c]) <= capacity[p] for p in P","sum(p in P, energy[p,c]) >= demand[c] for c in C","sum(p in P, participates[p,c]) >= 2 for c in C","energy[p,c] >= min_delivery[p] * participates[p,c] for (p,c) in P x C","energy[p,c] <= capacity[p] * participates[p,c] for (p,c) in P x C"],"objective":"minimize sum((p,c) in P x C, cost[p][c] * energy[p,c])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, 2)
    model.contracts = pyo.RangeSet(0, 3)

    model.capacity_data = pyo.Param(
        model.producers,
        initialize=lambda _, producer: capacity[producer],
    )
    model.demand_data = pyo.Param(
        model.contracts,
        initialize=lambda _, contract: demand[contract],
    )
    model.minimum_delivery_data = pyo.Param(
        model.producers,
        initialize=lambda _, producer: min_delivery[producer],
    )
    model.cost_data = pyo.Param(
        model.producers,
        model.contracts,
        initialize=lambda _, producer, contract: cost[producer][contract],
    )

    model.energy = pyo.Var(
        model.producers,
        model.contracts,
        domain=pyo.NonNegativeReals,
    )
    model.participates = pyo.Var(
        model.producers,
        model.contracts,
        domain=pyo.Binary,
    )

    def capacity_rule(problem, producer):
        return (
            sum(
                problem.energy[producer, contract]
                for contract in problem.contracts
            )
            <= problem.capacity_data[producer]
        )

    model.capacity_limits = pyo.Constraint(
        model.producers, rule=capacity_rule
    )

    def demand_rule(problem, contract):
        return (
            sum(
                problem.energy[producer, contract]
                for producer in problem.producers
            )
            >= problem.demand_data[contract]
        )

    model.demand_requirements = pyo.Constraint(
        model.contracts, rule=demand_rule
    )

    def contributor_rule(problem, contract):
        return (
            sum(
                problem.participates[producer, contract]
                for producer in problem.producers
            )
            >= 2
        )

    model.contributor_requirements = pyo.Constraint(
        model.contracts, rule=contributor_rule
    )

    def minimum_delivery_rule(problem, producer, contract):
        return (
            problem.energy[producer, contract]
            >= problem.minimum_delivery_data[producer]
            * problem.participates[producer, contract]
        )

    model.minimum_delivery_limits = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=minimum_delivery_rule,
    )

    def participation_link_rule(problem, producer, contract):
        return (
            problem.energy[producer, contract]
            <= problem.capacity_data[producer]
            * problem.participates[producer, contract]
        )

    model.participation_links = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=participation_link_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_data[producer, contract]
            * model.energy[producer, contract]
            for producer in model.producers
            for contract in model.contracts
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, RuntimeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
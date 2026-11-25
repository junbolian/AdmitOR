# IR: {"sets":{"P":[0,1,2,3],"C":[0,1,2,3,4]},"params":{"cost":"P x C -> real","capacity":"P -> nonnegative real","demand":"C -> nonnegative real","min_producers":"C -> nonnegative integer","min_delivery":"P -> nonnegative real"},"variables":{"delivery[p,c]":"nonnegative continuous","assigned[p,c]":"binary"},"constraints":["sum_c delivery[p,c] <= capacity[p] for each p","sum_p delivery[p,c] >= demand[c] for each c","sum_p assigned[p,c] >= min_producers[c] for each c","delivery[p,c] >= min_delivery[p]*assigned[p,c] for each p,c","delivery[p,c] <= capacity[p]*assigned[p,c] for each p,c"],"objective":"minimize sum_{p,c} cost[p,c]*delivery[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, 3)
    model.contracts = pyo.RangeSet(0, 4)

    model.unit_cost = pyo.Param(
        model.producers,
        model.contracts,
        initialize=lambda mdl, producer, contract: params["cost"][producer][contract],
        within=pyo.Reals,
    )
    model.generation_capacity = pyo.Param(
        model.producers,
        initialize=lambda mdl, producer: params["capacity"][producer],
        within=pyo.NonNegativeReals,
    )
    model.required_delivery = pyo.Param(
        model.contracts,
        initialize=lambda mdl, contract: params["demand"][contract],
        within=pyo.NonNegativeReals,
    )
    model.required_producers = pyo.Param(
        model.contracts,
        initialize=lambda mdl, contract: params["min_producers"][contract],
        within=pyo.NonNegativeIntegers,
    )
    model.assignment_minimum = pyo.Param(
        model.producers,
        initialize=lambda mdl, producer: params["min_delivery"][producer],
        within=pyo.NonNegativeReals,
    )

    model.delivery = pyo.Var(
        model.producers,
        model.contracts,
        domain=pyo.NonNegativeReals,
    )
    model.assigned = pyo.Var(
        model.producers,
        model.contracts,
        domain=pyo.Binary,
    )

    def capacity_rule(mdl, producer):
        return (
            sum(mdl.delivery[producer, contract] for contract in mdl.contracts)
            <= mdl.generation_capacity[producer]
        )

    model.capacity_limits = pyo.Constraint(
        model.producers, rule=capacity_rule
    )

    def demand_rule(mdl, contract):
        return (
            sum(mdl.delivery[producer, contract] for producer in mdl.producers)
            >= mdl.required_delivery[contract]
        )

    model.demand_requirements = pyo.Constraint(
        model.contracts, rule=demand_rule
    )

    def producer_count_rule(mdl, contract):
        return (
            sum(mdl.assigned[producer, contract] for producer in mdl.producers)
            >= mdl.required_producers[contract]
        )

    model.producer_count_requirements = pyo.Constraint(
        model.contracts, rule=producer_count_rule
    )

    def minimum_delivery_rule(mdl, producer, contract):
        return (
            mdl.delivery[producer, contract]
            >= mdl.assignment_minimum[producer] * mdl.assigned[producer, contract]
        )

    model.minimum_assignment_deliveries = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=minimum_delivery_rule,
    )

    def assignment_link_rule(mdl, producer, contract):
        return (
            mdl.delivery[producer, contract]
            <= mdl.generation_capacity[producer] * mdl.assigned[producer, contract]
        )

    model.assignment_capacity_links = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=assignment_link_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[producer, contract] * model.delivery[producer, contract]
            for producer in model.producers
            for contract in model.contracts
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
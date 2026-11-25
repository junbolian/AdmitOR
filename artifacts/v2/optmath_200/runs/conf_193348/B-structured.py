# IR: {"sets":{"P":"0..3","C":"0..5"},"params":{"producer_capacity":"P","contract_demand":"C","contract_min_producers":"C","producer_min_delivery":"P","cost":"P x C, nested or flat producer-major"},"variables":{"delivery[P,C]":"continuous nonnegative","serves[P,C]":"binary"},"constraints":["sum_c delivery[p,c] <= producer_capacity[p] for each p","sum_p delivery[p,c] >= contract_demand[c] for each c","sum_p serves[p,c] >= contract_min_producers[c] for each c","delivery[p,c] >= producer_min_delivery[p]*serves[p,c] for each p,c","delivery[p,c] <= producer_capacity[p]*serves[p,c] for each p,c"],"objective":"minimize sum_p,c cost[p,c]*delivery[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    contract_min_producers = params["contract_min_producers"]
    producer_min_delivery = params["producer_min_delivery"]
    cost_data = params["cost"]

    # Accept either 24 producer-major entries or a 4-by-6 matrix.
    if len(cost_data) == 24:
        unit_cost = {
            (producer, contract): cost_data[6 * producer + contract]
            for producer in range(4)
            for contract in range(6)
        }
    else:
        unit_cost = {
            (producer, contract): cost_data[producer][contract]
            for producer in range(4)
            for contract in range(6)
        }

    model = pyo.ConcreteModel()
    model.producers = pyo.RangeSet(0, 3)
    model.contracts = pyo.RangeSet(0, 5)

    model.capacity_data = pyo.Param(
        model.producers,
        initialize={
            producer: producer_capacity[producer]
            for producer in range(4)
        },
    )
    model.demand_data = pyo.Param(
        model.contracts,
        initialize={
            contract: contract_demand[contract]
            for contract in range(6)
        },
    )
    model.minimum_producer_data = pyo.Param(
        model.contracts,
        initialize={
            contract: contract_min_producers[contract]
            for contract in range(6)
        },
    )
    model.minimum_delivery_data = pyo.Param(
        model.producers,
        initialize={
            producer: producer_min_delivery[producer]
            for producer in range(4)
        },
    )
    model.unit_cost_data = pyo.Param(
        model.producers,
        model.contracts,
        initialize=unit_cost,
    )

    model.delivery = pyo.Var(
        model.producers,
        model.contracts,
        domain=pyo.NonNegativeReals,
    )
    model.serves = pyo.Var(
        model.producers,
        model.contracts,
        domain=pyo.Binary,
    )

    def capacity_rule(instance, producer):
        return (
            sum(
                instance.delivery[producer, contract]
                for contract in instance.contracts
            )
            <= instance.capacity_data[producer]
        )

    model.capacity_limits = pyo.Constraint(
        model.producers, rule=capacity_rule
    )

    def demand_rule(instance, contract):
        return (
            sum(
                instance.delivery[producer, contract]
                for producer in instance.producers
            )
            >= instance.demand_data[contract]
        )

    model.demand_requirements = pyo.Constraint(
        model.contracts, rule=demand_rule
    )

    def producer_count_rule(instance, contract):
        return (
            sum(
                instance.serves[producer, contract]
                for producer in instance.producers
            )
            >= instance.minimum_producer_data[contract]
        )

    model.producer_count_requirements = pyo.Constraint(
        model.contracts, rule=producer_count_rule
    )

    def minimum_delivery_rule(instance, producer, contract):
        return (
            instance.delivery[producer, contract]
            >= instance.minimum_delivery_data[producer]
            * instance.serves[producer, contract]
        )

    model.minimum_delivery_links = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=minimum_delivery_rule,
    )

    def maximum_delivery_rule(instance, producer, contract):
        return (
            instance.delivery[producer, contract]
            <= instance.capacity_data[producer]
            * instance.serves[producer, contract]
        )

    model.maximum_delivery_links = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=maximum_delivery_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost_data[producer, contract]
            * model.delivery[producer, contract]
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
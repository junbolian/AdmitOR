# IR: {"sets":{"P":"0..5","C":"0..6"},"params":{"producer_capacity":"P -> nonnegative real","contract_demand":"C -> nonnegative real","min_contributors":"C -> nonnegative integer, immutable","producer_min_delivery":"P -> nonnegative real","cost_matrix":"P x C -> real"},"variables":{"delivery[p,c]":"nonnegative continuous","contributes[p,c]":"binary"},"constraints":["forall p: sum_c delivery[p,c] <= producer_capacity[p]","forall c: sum_p delivery[p,c] >= contract_demand[c]","forall c: sum_p contributes[p,c] >= min_contributors[c]","forall p,c: delivery[p,c] >= producer_min_delivery[p] * contributes[p,c]","forall p,c: delivery[p,c] <= producer_capacity[p] * contributes[p,c]"],"objective":"minimize sum_p,c cost_matrix[p,c] * delivery[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, 5)
    model.contracts = pyo.RangeSet(0, 6)

    model.producer_capacity = pyo.Param(
        model.producers,
        initialize=lambda model, producer: params["producer_capacity"][producer],
        within=pyo.NonNegativeReals,
        mutable=False,
    )
    model.contract_demand = pyo.Param(
        model.contracts,
        initialize=lambda model, contract: params["contract_demand"][contract],
        within=pyo.NonNegativeReals,
        mutable=False,
    )
    model.min_contributors = pyo.Param(
        model.contracts,
        initialize=lambda model, contract: params["min_contributors"][contract],
        within=pyo.NonNegativeIntegers,
        mutable=False,
    )
    model.producer_min_delivery = pyo.Param(
        model.producers,
        initialize=lambda model, producer: params["producer_min_delivery"][producer],
        within=pyo.NonNegativeReals,
        mutable=False,
    )
    model.cost_matrix = pyo.Param(
        model.producers,
        model.contracts,
        initialize=lambda model, producer, contract: params["cost_matrix"][producer][
            contract
        ],
        within=pyo.Reals,
        mutable=False,
    )

    model.delivery = pyo.Var(
        model.producers,
        model.contracts,
        domain=pyo.NonNegativeReals,
    )
    model.contributes = pyo.Var(
        model.producers,
        model.contracts,
        domain=pyo.Binary,
    )

    def capacity_rule(model, producer):
        return (
            sum(
                model.delivery[producer, contract]
                for contract in model.contracts
            )
            <= model.producer_capacity[producer]
        )

    model.capacity_limits = pyo.Constraint(
        model.producers,
        rule=capacity_rule,
    )

    def demand_rule(model, contract):
        return (
            sum(
                model.delivery[producer, contract]
                for producer in model.producers
            )
            >= model.contract_demand[contract]
        )

    model.demand_requirements = pyo.Constraint(
        model.contracts,
        rule=demand_rule,
    )

    def contributor_rule(model, contract):
        return (
            sum(
                model.contributes[producer, contract]
                for producer in model.producers
            )
            >= model.min_contributors[contract]
        )

    model.contributor_requirements = pyo.Constraint(
        model.contracts,
        rule=contributor_rule,
    )

    def minimum_delivery_rule(model, producer, contract):
        return (
            model.delivery[producer, contract]
            >= model.producer_min_delivery[producer]
            * model.contributes[producer, contract]
        )

    model.minimum_deliveries = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=minimum_delivery_rule,
    )

    def activation_rule(model, producer, contract):
        return (
            model.delivery[producer, contract]
            <= model.producer_capacity[producer]
            * model.contributes[producer, contract]
        )

    model.delivery_activation = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=activation_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_matrix[producer, contract]
            * model.delivery[producer, contract]
            for producer in model.producers
            for contract in model.contracts
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        # Objective retrieval below remains the sole success criterion.
        if "feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
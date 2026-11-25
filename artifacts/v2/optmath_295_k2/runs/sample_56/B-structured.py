# IR: {"sets":{"P":[0,1,2],"C":[0,1,2,3]},"params":{"capacity[p]":"params[capacity_P{p}]","demand[c]":"params[demand_C{c}]","min_delivery[p]":"params[min_delivery_P{p}]","cost[p,c]":"params[cost_P{p}_C{c}]"},"variables":{"delivery[p,c]":"nonnegative continuous","serves[p,c]":"binary"},"constraints":["sum_c delivery[p,c] <= capacity[p] for each p","sum_p delivery[p,c] >= demand[c] for each c","sum_p serves[p,c] >= 2 for each c","delivery[p,c] >= min_delivery[p]*serves[p,c] for each p,c","delivery[p,c] <= capacity[p]*serves[p,c] for each p,c"],"objective":"minimize sum_{p,c} cost[p,c]*delivery[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = {
        0: params["capacity_P0"],
        1: params["capacity_P1"],
        2: params["capacity_P2"],
    }
    demand = {
        0: params["demand_C0"],
        1: params["demand_C1"],
        2: params["demand_C2"],
        3: params["demand_C3"],
    }
    min_delivery = {
        0: params["min_delivery_P0"],
        1: params["min_delivery_P1"],
        2: params["min_delivery_P2"],
    }
    cost = {
        (0, 0): params["cost_P0_C0"],
        (0, 1): params["cost_P0_C1"],
        (0, 2): params["cost_P0_C2"],
        (0, 3): params["cost_P0_C3"],
        (1, 0): params["cost_P1_C0"],
        (1, 1): params["cost_P1_C1"],
        (1, 2): params["cost_P1_C2"],
        (1, 3): params["cost_P1_C3"],
        (2, 0): params["cost_P2_C0"],
        (2, 1): params["cost_P2_C1"],
        (2, 2): params["cost_P2_C2"],
        (2, 3): params["cost_P2_C3"],
    }

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, 2)
    model.C = pyo.RangeSet(0, 3)

    model.capacity = pyo.Param(model.P, initialize=capacity)
    model.demand = pyo.Param(model.C, initialize=demand)
    model.min_delivery = pyo.Param(model.P, initialize=min_delivery)
    model.cost = pyo.Param(model.P, model.C, initialize=cost)

    model.delivery = pyo.Var(
        model.P, model.C, domain=pyo.NonNegativeReals
    )
    model.serves = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def capacity_rule(instance, producer):
        return (
            sum(instance.delivery[producer, contract]
                for contract in instance.C)
            <= instance.capacity[producer]
        )

    model.capacity_limits = pyo.Constraint(
        model.P, rule=capacity_rule
    )

    def demand_rule(instance, contract):
        return (
            sum(instance.delivery[producer, contract]
                for producer in instance.P)
            >= instance.demand[contract]
        )

    model.demand_requirements = pyo.Constraint(
        model.C, rule=demand_rule
    )

    def producer_count_rule(instance, contract):
        return (
            sum(instance.serves[producer, contract]
                for producer in instance.P)
            >= 2
        )

    model.producer_count_requirements = pyo.Constraint(
        model.C, rule=producer_count_rule
    )

    def minimum_delivery_rule(instance, producer, contract):
        return (
            instance.delivery[producer, contract]
            >= instance.min_delivery[producer]
            * instance.serves[producer, contract]
        )

    model.minimum_delivery_links = pyo.Constraint(
        model.P, model.C, rule=minimum_delivery_rule
    )

    def maximum_delivery_rule(instance, producer, contract):
        return (
            instance.delivery[producer, contract]
            <= instance.capacity[producer]
            * instance.serves[producer, contract]
        )

    model.maximum_delivery_links = pyo.Constraint(
        model.P, model.C, rule=maximum_delivery_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[producer, contract]
            * model.delivery[producer, contract]
            for producer in model.P
            for contract in model.C
        ),
        sense=pyo.minimize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi can raise when no feasible solution can be loaded.
        # Objective retrieval below remains the sole success test.
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "solver_failed" if solver_failed
                else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}
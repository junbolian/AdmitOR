# IR: {"sets":{"P":[0,1,2],"C":[0,1,2,3]},"params":{"capacity":["capacity_P0","capacity_P1","capacity_P2"],"demand":["demand_C0","demand_C1","demand_C2","demand_C3"],"min_delivery":["min_delivery_P0","min_delivery_P1","min_delivery_P2"],"cost":[["cost_P0_C0","cost_P0_C1","cost_P0_C2","cost_P0_C3"],["cost_P1_C0","cost_P1_C1","cost_P1_C2","cost_P1_C3"],["cost_P2_C0","cost_P2_C1","cost_P2_C2","cost_P2_C3"]]},"variables":{"delivery[p,c]":"NonNegativeReals","serves[p,c]":"Binary"},"constraints":["forall p: sum(c,delivery[p,c]) <= capacity[p]","forall c: sum(p,delivery[p,c]) >= demand[c]","forall c: sum(p,serves[p,c]) >= 2","forall p,c: delivery[p,c] >= min_delivery[p]*serves[p,c]","forall p,c: delivery[p,c] <= capacity[p]*serves[p,c]"],"objective":"minimize sum(p,c,cost[p,c]*delivery[p,c])"}

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
    model.P = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.C = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)

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
            sum(instance.delivery[producer, contract] for contract in instance.C)
            <= instance.capacity[producer]
        )

    model.capacity_limits = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(instance, contract):
        return (
            sum(instance.delivery[producer, contract] for producer in instance.P)
            >= instance.demand[contract]
        )

    model.demand_requirements = pyo.Constraint(model.C, rule=demand_rule)

    def producer_count_rule(instance, contract):
        return (
            sum(instance.serves[producer, contract] for producer in instance.P)
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

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
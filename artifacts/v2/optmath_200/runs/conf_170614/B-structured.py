# IR: {"sets":{"P":[0,1,2],"C":[0,1,2,3]},"params":{"capacity":["capacity_0","capacity_1","capacity_2"],"demand":["demand_0","demand_1","demand_2","demand_3"],"cost":[["cost_0_0","cost_0_1","cost_0_2","cost_0_3"],["cost_1_0","cost_1_1","cost_1_2","cost_1_3"],["cost_2_0","cost_2_1","cost_2_2","cost_2_3"]],"min_delivery":["min_delivery_0","min_delivery_1","min_delivery_2"],"min_producers_per_contract":"min_producers_per_contract"},"variables":{"delivery[p,c]":"NonNegativeReals","assigned[p,c]":"Binary"},"constraints":["sum(c in C,delivery[p,c]) <= capacity[p] for p in P","sum(p in P,delivery[p,c]) >= demand[c] for c in C","delivery[p,c] >= min_delivery[p]*assigned[p,c] for (p,c) in P x C","delivery[p,c] <= capacity[p]*assigned[p,c] for (p,c) in P x C","sum(p in P,assigned[p,c]) >= min_producers_per_contract for c in C"],"objective":{"sense":"minimize","expression":"sum((p,c) in P x C,cost[p,c]*delivery[p,c])"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_data = {
        0: params["capacity_0"],
        1: params["capacity_1"],
        2: params["capacity_2"],
    }
    demand_data = {
        0: params["demand_0"],
        1: params["demand_1"],
        2: params["demand_2"],
        3: params["demand_3"],
    }
    cost_data = {
        (0, 0): params["cost_0_0"],
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 3): params["cost_0_3"],
        (1, 0): params["cost_1_0"],
        (1, 1): params["cost_1_1"],
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
        (2, 2): params["cost_2_2"],
        (2, 3): params["cost_2_3"],
    }
    min_delivery_data = {
        0: params["min_delivery_0"],
        1: params["min_delivery_1"],
        2: params["min_delivery_2"],
    }

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.C = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)

    model.capacity = pyo.Param(model.P, initialize=capacity_data)
    model.demand = pyo.Param(model.C, initialize=demand_data)
    model.cost = pyo.Param(model.P, model.C, initialize=cost_data)
    model.min_delivery = pyo.Param(model.P, initialize=min_delivery_data)
    model.min_producers_per_contract = pyo.Param(
        initialize=params["min_producers_per_contract"]
    )

    model.delivery = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.assigned = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def capacity_rule(block, producer):
        return (
            sum(block.delivery[producer, contract] for contract in block.C)
            <= block.capacity[producer]
        )

    model.capacity_limit = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(block, contract):
        return (
            sum(block.delivery[producer, contract] for producer in block.P)
            >= block.demand[contract]
        )

    model.demand_requirement = pyo.Constraint(model.C, rule=demand_rule)

    def minimum_delivery_rule(block, producer, contract):
        return (
            block.delivery[producer, contract]
            >= block.min_delivery[producer] * block.assigned[producer, contract]
        )

    model.minimum_delivery_link = pyo.Constraint(
        model.P, model.C, rule=minimum_delivery_rule
    )

    def assignment_upper_rule(block, producer, contract):
        return (
            block.delivery[producer, contract]
            <= block.capacity[producer] * block.assigned[producer, contract]
        )

    model.assignment_upper_link = pyo.Constraint(
        model.P, model.C, rule=assignment_upper_rule
    )

    def producer_count_rule(block, contract):
        return (
            sum(block.assigned[producer, contract] for producer in block.P)
            >= block.min_producers_per_contract
        )

    model.producer_count_requirement = pyo.Constraint(
        model.C, rule=producer_count_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[producer, contract] * model.delivery[producer, contract]
            for producer in model.P
            for contract in model.C
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
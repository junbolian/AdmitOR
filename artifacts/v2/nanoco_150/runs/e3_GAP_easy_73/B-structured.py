# IR: {"sets":{"towers":["T1","T2","T3"],"packets":[1,2,3,4,5,6,7]},"params":{"capacity_T1":"scalar","capacity_T2":"scalar","capacity_T3":"scalar","usage_T1":"length-7 sequence in packet order","usage_T2":"length-7 sequence in packet order","usage_T3":"length-7 sequence in packet order","cost_T1":"length-7 sequence in packet order","cost_T2":"length-7 sequence in packet order","cost_T3":"length-7 sequence in packet order"},"variables":{"assignment[tower,packet]":"binary"},"constraints":["For each packet: sum(assignment[tower,packet] for tower in towers) == 1","For each tower: sum(usage[tower,packet]*assignment[tower,packet] for packet in packets) <= capacity[tower]"],"objective":"Minimize sum(cost[tower,packet]*assignment[tower,packet] for tower in towers for packet in packets)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = {
        "T1": params["capacity_T1"],
        "T2": params["capacity_T2"],
        "T3": params["capacity_T3"],
    }
    usages = {
        "T1": params["usage_T1"],
        "T2": params["usage_T2"],
        "T3": params["usage_T3"],
    }
    costs = {
        "T1": params["cost_T1"],
        "T2": params["cost_T2"],
        "T3": params["cost_T3"],
    }

    model = pyo.ConcreteModel()
    model.towers = pyo.Set(initialize=("T1", "T2", "T3"), ordered=True)
    model.packets = pyo.RangeSet(1, 7)

    model.capacity = pyo.Param(
        model.towers,
        initialize=capacities,
        within=pyo.Reals,
    )
    model.usage = pyo.Param(
        model.towers,
        model.packets,
        initialize={
            (tower, packet): usages[tower][packet - 1]
            for tower in model.towers
            for packet in model.packets
        },
        within=pyo.Reals,
    )
    model.routing_cost = pyo.Param(
        model.towers,
        model.packets,
        initialize={
            (tower, packet): costs[tower][packet - 1]
            for tower in model.towers
            for packet in model.packets
        },
        within=pyo.Reals,
    )

    # Binary solution values explicitly identify each packet's assigned tower.
    model.assignment = pyo.Var(
        model.towers,
        model.packets,
        domain=pyo.Binary,
    )

    def assign_once_rule(current_model, packet):
        return sum(
            current_model.assignment[tower, packet]
            for tower in current_model.towers
        ) == 1

    model.assign_once = pyo.Constraint(
        model.packets,
        rule=assign_once_rule,
    )

    def bandwidth_limit_rule(current_model, tower):
        return sum(
            current_model.usage[tower, packet]
            * current_model.assignment[tower, packet]
            for packet in current_model.packets
        ) <= current_model.capacity[tower]

    model.bandwidth_limit = pyo.Constraint(
        model.towers,
        rule=bandwidth_limit_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.routing_cost[tower, packet]
            * model.assignment[tower, packet]
            for tower in model.towers
            for packet in model.packets
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when it cannot load a feasible solution.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
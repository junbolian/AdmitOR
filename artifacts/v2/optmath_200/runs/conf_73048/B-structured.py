# IR: {"sets":{"cities":"0..6","arcs":"[(i,j) for i in cities for j in cities if i != j], row-major"},"params":{"net_supply":"real[cities], from params['net_supply']","transport_cost":"real[arcs], from params['transport_cost'] in arc order","node_capacity":"real[cities], from params['node_capacity']","link_capacity":"real[arcs], from params['link_capacity'] in arc order"},"variables":{"flow":"nonnegative continuous[arcs]"},"constraints":{"balance":"forall i: sum(j != i, flow[i,j]) - sum(j != i, flow[j,i]) == net_supply[i]","incoming_capacity":"forall i: sum(j != i, flow[j,i]) <= node_capacity[i]","arc_capacity":"forall (i,j): flow[i,j] <= link_capacity[i,j]"},"objective":{"sense":"minimize","expression":"sum((i,j) in arcs, transport_cost[i,j] * flow[i,j])"}}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = list(range(7))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    net_supply = params["net_supply"]
    transport_cost = params["transport_cost"]
    node_capacity = params["node_capacity"]
    link_capacity = params["link_capacity"]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.net_supply = pyo.Param(
        model.cities,
        initialize={i: net_supply[i] for i in cities},
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.arcs,
        initialize={arc: transport_cost[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.node_capacity = pyo.Param(
        model.cities,
        initialize={i: node_capacity[i] for i in cities},
        within=pyo.Reals,
    )
    model.link_capacity = pyo.Param(
        model.arcs,
        initialize={arc: link_capacity[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(block, i):
        return (
            sum(block.flow[i, j] for j in block.cities if j != i)
            - sum(block.flow[j, i] for j in block.cities if j != i)
            == block.net_supply[i]
        )

    def incoming_capacity_rule(block, i):
        return (
            sum(block.flow[j, i] for j in block.cities if j != i)
            <= block.node_capacity[i]
        )

    def arc_capacity_rule(block, i, j):
        return block.flow[i, j] <= block.link_capacity[i, j]

    model.balance = pyo.Constraint(model.cities, rule=balance_rule)
    model.incoming_capacity = pyo.Constraint(
        model.cities, rule=incoming_capacity_rule
    )
    model.arc_capacity = pyo.Constraint(model.arcs, rule=arc_capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.flow[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"N":[0,1,2,3,4],"A":"{(i,j) in N x N: i != j}"},"params":{"d0":"params['net_outflow_demand_hub0']","d1":"params['net_outflow_demand_hub1']","s3":"params['net_inflow_supply_hub3']","s4":"params['net_inflow_supply_hub4']","F[i,j]":"params[f'fixed_cost_{i}_{j}']","U[i,j]":"params[f'capacity_{i}_{j}']","C[i,j]":"params[f'variable_cost_{i}_{j}']","b":"{0:d0,1:d1,2:0,3:-s3,4:-s4}"},"variables":{"flow[i,j]":"continuous nonnegative, (i,j) in A","opened[i,j]":"binary, (i,j) in A"},"constraints":["flow[i,j] <= U[i,j]*opened[i,j] for (i,j) in A","sum(flow[i,j] for j != i)-sum(flow[j,i] for j != i) == b[i] for i in N"],"objective":"minimize sum(F[i,j]*opened[i,j]+C[i,j]*flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.hubs = pyo.Set(initialize=range(5), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(5)
            for destination in range(5)
            if origin != destination
        ],
        ordered=True,
    )

    # Follow the stated net-flow directions literally:
    # hubs 0 and 1 have net outflow; hubs 3 and 4 have net inflow.
    model.net_outflow = pyo.Param(
        model.hubs,
        initialize={
            0: params["net_outflow_demand_hub0"],
            1: params["net_outflow_demand_hub1"],
            2: 0,
            3: -params["net_inflow_supply_hub3"],
            4: -params["net_inflow_supply_hub4"],
        },
        within=pyo.Reals,
    )

    model.fixed_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"fixed_cost_{origin}_{destination}"]
            for origin, destination in model.arcs
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"capacity_{origin}_{destination}"]
            for origin, destination in model.arcs
        },
        within=pyo.NonNegativeReals,
    )
    model.variable_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"variable_cost_{origin}_{destination}"]
            for origin, destination in model.arcs
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.opened = pyo.Var(model.arcs, domain=pyo.Binary)

    def capacity_rule(model, origin, destination):
        return (
            model.flow[origin, destination]
            <= model.capacity[origin, destination]
            * model.opened[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def balance_rule(model, hub):
        outgoing = sum(
            model.flow[hub, other]
            for other in model.hubs
            if other != hub
        )
        incoming = sum(
            model.flow[other, hub]
            for other in model.hubs
            if other != hub
        )
        return outgoing - incoming == model.net_outflow[hub]

    model.flow_balances = pyo.Constraint(model.hubs, rule=balance_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[origin, destination]
            * model.opened[origin, destination]
            + model.variable_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
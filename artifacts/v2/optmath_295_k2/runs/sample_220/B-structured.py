# IR: {"sets":{"H":[0,1,2,3,4],"E":"[(i,j) for i in H for j in H if i<j], lexicographic","A":"[(i,j) for i in H for j in H if i!=j]"},"params":{"inputs":["demand_0","demand_1","supply_2","supply_3","supply_4","fixed_cost_min","fixed_cost_max","variable_cost_min","variable_cost_max","capacity_min","capacity_max"],"b":"[demand_0,demand_1,-supply_2,-supply_3,-supply_4]","t[e]":"zero-based position of e in E divided by (|E|-1)","F[e]":"fixed_cost_min+t[e]*(fixed_cost_max-fixed_cost_min)","C[e]":"variable_cost_min+t[e]*(variable_cost_max-variable_cost_min)","U[e]":"capacity_min+t[e]*(capacity_max-capacity_min)"},"variables":{"y[e]":"binary, e in E","x[i,j]":"continuous nonnegative, (i,j) in A"},"constraints":["For each h in H: sum(x[i,h] for i!=h)-sum(x[h,j] for j!=h)=b[h]","For each (i,j) in E: x[i,j]+x[j,i]<=U[i,j]*y[i,j]"],"objective":"minimize sum(F[i,j]*y[i,j]+C[i,j]*(x[i,j]+x[j,i]) for (i,j) in E)"}
#
# Modeling assumptions: The problem supplies ranges, but no pair-specific
# data or generation rule. This implementation deterministically interpolates
# each range over lexicographically ordered unordered hub pairs. It assumes
# every pair is a candidate bidirectional connection, with one establishment
# cost and a capacity shared by flows in both directions.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_0 = float(params["demand_0"])
    demand_1 = float(params["demand_1"])
    supply_2 = float(params["supply_2"])
    supply_3 = float(params["supply_3"])
    supply_4 = float(params["supply_4"])
    fixed_cost_min = float(params["fixed_cost_min"])
    fixed_cost_max = float(params["fixed_cost_max"])
    variable_cost_min = float(params["variable_cost_min"])
    variable_cost_max = float(params["variable_cost_max"])
    capacity_min = float(params["capacity_min"])
    capacity_max = float(params["capacity_max"])

    hubs = list(range(5))
    edges = [(i, j) for i in hubs for j in hubs if i < j]
    arcs = [(i, j) for i in hubs for j in hubs if i != j]

    net_demand = {
        0: demand_0,
        1: demand_1,
        2: -supply_2,
        3: -supply_3,
        4: -supply_4,
    }

    interpolation = {
        edge: position / (len(edges) - 1)
        for position, edge in enumerate(edges)
    }
    fixed_cost = {
        edge: fixed_cost_min
        + interpolation[edge] * (fixed_cost_max - fixed_cost_min)
        for edge in edges
    }
    variable_cost = {
        edge: variable_cost_min
        + interpolation[edge] * (variable_cost_max - variable_cost_min)
        for edge in edges
    }
    capacity = {
        edge: capacity_min
        + interpolation[edge] * (capacity_max - capacity_min)
        for edge in edges
    }

    model = pyo.ConcreteModel()
    model.H = pyo.Set(initialize=hubs, ordered=True)
    model.E = pyo.Set(initialize=edges, dimen=2, ordered=True)
    model.A = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.net_demand = pyo.Param(
        model.H, initialize=net_demand, within=pyo.Reals
    )
    model.fixed_cost = pyo.Param(
        model.E, initialize=fixed_cost, within=pyo.Reals
    )
    model.variable_cost = pyo.Param(
        model.E, initialize=variable_cost, within=pyo.Reals
    )
    model.capacity = pyo.Param(
        model.E, initialize=capacity, within=pyo.Reals
    )

    model.y = pyo.Var(model.E, domain=pyo.Binary)
    model.x = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def flow_balance_rule(instance, hub):
        inflow = sum(
            instance.x[other, hub]
            for other in instance.H
            if other != hub
        )
        outflow = sum(
            instance.x[hub, other]
            for other in instance.H
            if other != hub
        )
        return inflow - outflow == instance.net_demand[hub]

    model.flow_balance = pyo.Constraint(
        model.H, rule=flow_balance_rule
    )

    def connection_capacity_rule(instance, i, j):
        return (
            instance.x[i, j] + instance.x[j, i]
            <= instance.capacity[i, j] * instance.y[i, j]
        )

    model.connection_capacity = pyo.Constraint(
        model.E, rule=connection_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[i, j] * model.y[i, j]
            + model.variable_cost[i, j]
            * (model.x[i, j] + model.x[j, i])
            for i, j in model.E
        ),
        sense=pyo.minimize,
    )

    # Appsi HiGHS can raise RuntimeError when no solution can be loaded.
    # Success is determined solely by objective-value retrieval below.
    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solve_failed" if solver_failed else "no_objective",
        }

    return {"objective": obj_val, "status": "optimal"}
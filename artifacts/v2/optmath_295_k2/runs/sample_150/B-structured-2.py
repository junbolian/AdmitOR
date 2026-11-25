# IR: {"sets":{"N":[0,1,2,3,4,5],"A":"{(i,j) in N x N: i != j}"},"params":{"b[i]":"params['supply_demand'][i]","F[i,j]":"params[f'fixed_cost_{i}_{j}']","c[i,j]":"params[f'variable_cost_{i}_{j}']","U[i,j]":"params[f'capacity_{i}_{j}']"},"variables":{"x[i,j]":"continuous nonnegative flow, (i,j) in A","y[i,j]":"binary connection established, (i,j) in A"},"constraints":["For each i in N: sum(x[i,j] for j != i) - sum(x[j,i] for j != i) = b[i]","For each (i,j) in A: x[i,j] <= U[i,j] * y[i,j]"],"objective":"minimize sum(F[i,j]*y[i,j] + c[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(6))
    arcs = tuple((i, j) for i in nodes for j in nodes if i != j)

    supply_demand = {
        i: params["supply_demand"][i]
        for i in nodes
    }
    fixed_cost = {
        (i, j): params[f"fixed_cost_{i}_{j}"]
        for i, j in arcs
    }
    variable_cost = {
        (i, j): params[f"variable_cost_{i}_{j}"]
        for i, j in arcs
    }
    capacity = {
        (i, j): params[f"capacity_{i}_{j}"]
        for i, j in arcs
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.net_supply = pyo.Param(
        model.nodes, initialize=supply_demand, within=pyo.Reals
    )
    model.fixed_cost = pyo.Param(
        model.arcs, initialize=fixed_cost, within=pyo.Reals
    )
    model.variable_cost = pyo.Param(
        model.arcs, initialize=variable_cost, within=pyo.Reals
    )
    model.capacity = pyo.Param(
        model.arcs, initialize=capacity, within=pyo.NonNegativeReals
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.connection = pyo.Var(model.arcs, domain=pyo.Binary)

    def balance_rule(mdl, i):
        outgoing = sum(
            mdl.flow[i, j] for j in mdl.nodes if j != i
        )
        incoming = sum(
            mdl.flow[j, i] for j in mdl.nodes if j != i
        )
        return outgoing - incoming == mdl.net_supply[i]

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=balance_rule
    )

    def capacity_rule(mdl, i, j):
        return (
            mdl.flow[i, j]
            <= mdl.capacity[i, j] * mdl.connection[i, j]
        )

    model.capacity_link = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[i, j] * model.connection[i, j]
            + model.variable_cost[i, j] * model.flow[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
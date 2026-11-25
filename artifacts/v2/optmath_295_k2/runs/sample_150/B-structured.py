# IR: {"sets":{"N":"{0,1,2,3,4,5}","A":"{(i,j) in N x N: i != j}"},"params":{"b[i]":"params['supply_demand'][i]","f[i,j]":"params[f'fixed_cost_{i}_{j}']","c[i,j]":"params[f'variable_cost_{i}_{j}']","u[i,j]":"params[f'capacity_{i}_{j}']"},"variables":{"x[i,j]":"continuous, nonnegative, for (i,j) in A","y[i,j]":"binary, for (i,j) in A"},"constraints":["sum(x[i,j] for j != i) - sum(x[j,i] for j != i) == b[i], for i in N","x[i,j] <= u[i,j]*y[i,j], for (i,j) in A"],"objective":"minimize sum(f[i,j]*y[i,j] + c[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = range(6)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    supply_demand = params["supply_demand"]
    fixed_cost = {
        (i, j): params[f"fixed_cost_{i}_{j}"] for i, j in arcs
    }
    variable_cost = {
        (i, j): params[f"variable_cost_{i}_{j}"] for i, j in arcs
    }
    capacity = {
        (i, j): params[f"capacity_{i}_{j}"] for i, j in arcs
    }

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.b = pyo.Param(
        model.N,
        initialize={i: supply_demand[i] for i in nodes},
        within=pyo.Reals,
    )
    model.f = pyo.Param(model.A, initialize=fixed_cost, within=pyo.Reals)
    model.c = pyo.Param(model.A, initialize=variable_cost, within=pyo.Reals)
    model.u = pyo.Param(
        model.A, initialize=capacity, within=pyo.NonNegativeReals
    )

    model.x = pyo.Var(model.A, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.A, domain=pyo.Binary)

    def flow_balance_rule(network, i):
        return (
            sum(network.x[i, j] for j in network.N if j != i)
            - sum(network.x[j, i] for j in network.N if j != i)
            == network.b[i]
        )

    model.flow_balance = pyo.Constraint(model.N, rule=flow_balance_rule)

    def connection_capacity_rule(network, i, j):
        return network.x[i, j] <= network.u[i, j] * network.y[i, j]

    model.connection_capacity = pyo.Constraint(
        model.A, rule=connection_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.f[i, j] * model.y[i, j]
            + model.c[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this specific error when no solution can be loaded.
        # Other runtime errors are unexpected and must propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
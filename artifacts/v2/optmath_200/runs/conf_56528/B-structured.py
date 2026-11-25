# IR: {"sets":{"N":"{0,...,6}","A":"{(i,j) in N x N: i != j}"},"params":{"supply_node0":"real, from params","demand_node6":"real, from params","cost_matrix":"7x7 real matrix, from params; diagonal ignored"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["For each i in N: sum_j x[i,j] - sum_j x[j,i] = supply_node0 if i=0, -demand_node6 if i=6, and 0 otherwise."],"objective":"Minimize sum_(i,j) in A cost_matrix[i][j] * x[i,j]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, 6)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(7)
            for j in range(7)
            if i != j
        ],
    )

    model.supply = pyo.Param(
        initialize=params["supply_node0"],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        initialize=params["demand_node6"],
        within=pyo.Reals,
    )
    model.route_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params["cost_matrix"][i][j]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.route_used = pyo.Var(model.arcs, domain=pyo.Binary)

    def flow_balance_rule(instance, i):
        outgoing = sum(
            instance.route_used[i, j]
            for j in instance.nodes
            if j != i
        )
        incoming = sum(
            instance.route_used[j, i]
            for j in instance.nodes
            if j != i
        )

        if i == 0:
            required_net_outflow = instance.supply
        elif i == 6:
            required_net_outflow = -instance.demand
        else:
            required_net_outflow = 0

        return outgoing - incoming == required_net_outflow

    model.flow_balance = pyo.Constraint(
        model.nodes,
        rule=flow_balance_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.route_used[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
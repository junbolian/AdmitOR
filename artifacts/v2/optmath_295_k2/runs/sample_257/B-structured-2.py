# IR: {"sets":{"N":"{0,...,7}","A":"{(i,j) in N x N: i != j}"},"params":{"c[i,j]":"params[f'c_{i}_{j}'] for (i,j) in A","supply_node0":"params['supply_node0']","demand_node7":"params['demand_node7']"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["sum_j x[0,j] - sum_i x[i,0] = supply_node0","sum_j x[k,j] - sum_i x[i,k] = 0 for k in {1,...,6}","sum_i x[i,7] - sum_j x[7,j] = demand_node7"],"objective":"minimize sum_{(i,j) in A} c[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(8)
            for j in range(8)
            if i != j
        ],
    )

    model.route_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"c_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )
    model.source_supply = pyo.Param(
        initialize=params["supply_node0"], within=pyo.Reals
    )
    model.destination_demand = pyo.Param(
        initialize=params["demand_node7"], within=pyo.Reals
    )

    model.route_used = pyo.Var(model.arcs, domain=pyo.Binary)

    def balance_rule(instance, node):
        outgoing = sum(
            instance.route_used[node, j]
            for j in instance.nodes
            if j != node
        )
        incoming = sum(
            instance.route_used[i, node]
            for i in instance.nodes
            if i != node
        )
        if node == 0:
            return outgoing - incoming == instance.source_supply
        if node == 7:
            return incoming - outgoing == instance.destination_demand
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.route_used[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    # HiGHS may raise RuntimeError when no feasible solution can be loaded.
    # Success is determined only by retrieving the objective below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "failed"}

    return {"objective": obj_val, "status": "optimal"}
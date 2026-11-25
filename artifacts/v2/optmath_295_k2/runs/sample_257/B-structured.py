# IR: {"sets":{"N":"0..7","A":"{(i,j) in N x N: i != j}"},"params":{"c[i,j]":"params['c_'+str(i)+'_'+str(j)] for (i,j) in A","supply":"params['supply_node0']","demand":"params['demand_node7']"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["sum_j x[0,j] - sum_j x[j,0] = supply","sum_j x[7,j] - sum_j x[j,7] = -demand","sum_{j != i} x[i,j] - sum_{j != i} x[j,i] = 0 for i in 1..6"],"objective":"minimize sum_{(i,j) in A} c[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j) for i in range(8) for j in range(8) if i != j
        ],
    )

    model.route_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"c_{i}_{j}"] for i, j in model.arcs
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

    def flow_balance_rule(block, i):
        net_outflow = sum(
            block.route_used[i, j] for j in block.nodes if j != i
        ) - sum(
            block.route_used[j, i] for j in block.nodes if j != i
        )
        if i == 0:
            return net_outflow == block.source_supply
        if i == 7:
            return net_outflow == -block.destination_demand
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=flow_balance_rule
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
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
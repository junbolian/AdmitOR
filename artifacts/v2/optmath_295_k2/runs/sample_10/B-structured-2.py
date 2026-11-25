# IR: {"sets":{"N":[0,1,2,3,4,5,6],"I":[1,2,3,4,5],"A":"{(i,j) in N x N : i != j}"},"params":{"arc_cost_i_j":"params['arc_cost_<i>_<j>'] for every (i,j) in A","supply_node_0":"params['supply_node_0']","demand_node_6":"params['demand_node_6']","balance_nodes_1_5":"params['balance_nodes_1_5'] (required to be zero)"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["sum_j x[0,j] - sum_i x[i,0] = supply_node_0","sum_i x[i,6] - sum_j x[6,j] = demand_node_6","sum_i x[i,k] - sum_j x[k,j] = balance_nodes_1_5 for k in I","balance_nodes_1_5 = 0"],"objective":"minimize sum_(i,j) in A arc_cost_i_j * x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(7), ordered=True)
    model.intermediate_nodes = pyo.Set(initialize=range(1, 6), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.nodes
            for j in model.nodes
            if i != j
        ],
    )

    model.arc_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"arc_cost_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )
    model.source_supply = pyo.Param(
        initialize=params["supply_node_0"],
        within=pyo.Reals,
    )
    model.destination_demand = pyo.Param(
        initialize=params["demand_node_6"],
        within=pyo.Reals,
    )
    model.intermediate_balance = pyo.Param(
        initialize=params["balance_nodes_1_5"],
        within=pyo.Reals,
        mutable=True,
    )

    model.route_used = pyo.Var(model.arcs, domain=pyo.Binary)

    model.source_flow = pyo.Constraint(
        expr=(
            sum(model.route_used[0, j] for j in model.nodes if j != 0)
            - sum(model.route_used[i, 0] for i in model.nodes if i != 0)
            == model.source_supply
        )
    )

    model.destination_flow = pyo.Constraint(
        expr=(
            sum(model.route_used[i, 6] for i in model.nodes if i != 6)
            - sum(model.route_used[6, j] for j in model.nodes if j != 6)
            == model.destination_demand
        )
    )

    def intermediate_flow_rule(network, k):
        return (
            sum(network.route_used[i, k] for i in network.nodes if i != k)
            - sum(network.route_used[k, j] for j in network.nodes if j != k)
            == network.intermediate_balance
        )

    model.intermediate_flow = pyo.Constraint(
        model.intermediate_nodes,
        rule=intermediate_flow_rule,
    )
    model.zero_intermediate_balance = pyo.Constraint(
        expr=model.intermediate_balance == 0
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_cost[i, j] * model.route_used[i, j]
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
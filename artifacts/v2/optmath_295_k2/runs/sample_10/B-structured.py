# IR: {"sets":{"N":[0,1,2,3,4,5,6],"I":[1,2,3,4,5],"A":"{(i,j): i,j in N, i!=j}"},"params":{"arc_cost_i_j":"params[f'arc_cost_{i}_{j}'] for (i,j) in A","supply_node_0":"params['supply_node_0']","demand_node_6":"params['demand_node_6']","balance_nodes_1_5":"params['balance_nodes_1_5'] (required to equal zero)"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":{"source":"sum(j!=0,x[0,j])-sum(i!=0,x[i,0])=supply_node_0","destination":"sum(i!=6,x[i,6])-sum(j!=6,x[6,j])=demand_node_6","intermediate":"sum(i!=k,x[i,k])-sum(j!=k,x[k,j])=balance_nodes_1_5 for k in I"},"objective":"minimize sum((i,j) in A,arc_cost_i_j*x[i,j])"}

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
            for i in range(7)
            for j in range(7)
            if i != j
        ],
        ordered=True,
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

    intermediate_balance = params["balance_nodes_1_5"]
    if intermediate_balance != 0:
        return {"objective": None, "status": "invalid_balance"}

    model.intermediate_balance = pyo.Param(
        initialize=intermediate_balance,
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    model.source_flow = pyo.Constraint(
        expr=(
            sum(model.x[0, j] for j in model.nodes if j != 0)
            - sum(model.x[i, 0] for i in model.nodes if i != 0)
            == model.source_supply
        )
    )

    model.destination_flow = pyo.Constraint(
        expr=(
            sum(model.x[i, 6] for i in model.nodes if i != 6)
            - sum(model.x[6, j] for j in model.nodes if j != 6)
            == model.destination_demand
        )
    )

    def intermediate_flow_rule(current_model, k):
        return (
            sum(
                current_model.x[i, k]
                for i in current_model.nodes
                if i != k
            )
            - sum(
                current_model.x[k, j]
                for j in current_model.nodes
                if j != k
            )
            == current_model.intermediate_balance
        )

    model.intermediate_flow = pyo.Constraint(
        model.intermediate_nodes,
        rule=intermediate_flow_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
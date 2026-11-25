# IR: {"sets":{"N":"0..num_nodes_total-1","D":"1..num_drop_zones","A":"{(i,j): i in N, j in D, i != j}"},"params":{"num_nodes_total":"total node count","num_drop_zones":"drop-zone count; num_nodes_total = num_drop_zones + 1","cost_matrix":"symmetric edge costs","branch_capacity":"maximum drop zones per root branch"},"variables":{"x[i,j]":"binary; select directed parent arc","flow[i,j]":"nonnegative continuous; drop-zone demand carried by arc"},"constraints":["Each j in D has exactly one incoming selected arc.","For each j in D: incoming flow - outgoing flow = 1.","Root outgoing flow = num_drop_zones.","For each (i,j) in A: flow[i,j] <= branch_capacity*x[i,j]."],"objective":"minimize sum(cost_matrix[i][j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes_total = params["num_nodes_total"]
    num_drop_zones = params["num_drop_zones"]
    branch_capacity = params["branch_capacity"]
    cost_matrix = params["cost_matrix"]

    if num_nodes_total != num_drop_zones + 1:
        raise ValueError("Node counts must include exactly one base.")

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(
        initialize=range(num_nodes_total),
        ordered=True,
    )
    model.drop_zones = pyo.Set(
        initialize=range(1, num_drop_zones + 1),
        ordered=True,
    )
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(num_nodes_total)
            for destination in range(1, num_drop_zones + 1)
            if origin != destination
        ],
    )

    model.capacity = pyo.Param(
        initialize=branch_capacity,
        within=pyo.NonNegativeReals,
    )
    model.edge_cost = pyo.Param(
        model.arcs,
        initialize=lambda mdl, origin, destination: cost_matrix[origin][destination],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def one_parent_rule(mdl, destination):
        return sum(
            mdl.x[origin, destination]
            for origin in mdl.nodes
            if origin != destination
        ) == 1

    model.one_parent = pyo.Constraint(
        model.drop_zones,
        rule=one_parent_rule,
    )

    def flow_balance_rule(mdl, node):
        incoming = sum(
            mdl.flow[origin, node]
            for origin in mdl.nodes
            if origin != node
        )
        outgoing = sum(
            mdl.flow[node, destination]
            for destination in mdl.drop_zones
            if destination != node
        )
        return incoming - outgoing == 1

    model.zone_flow_balance = pyo.Constraint(
        model.drop_zones,
        rule=flow_balance_rule,
    )

    model.root_flow_balance = pyo.Constraint(
        expr=sum(
            model.flow[0, destination]
            for destination in model.drop_zones
        ) == num_drop_zones
    )

    model.arc_capacity = pyo.Constraint(
        model.arcs,
        rule=lambda mdl, origin, destination: (
            mdl.flow[origin, destination]
            <= mdl.capacity * mdl.x[origin, destination]
        ),
    )

    # Positive demand eliminates disconnected cycles. One parent per zone
    # therefore gives a rooted tree. Flow on a root arc equals the number
    # of zones in that entire branch, enforcing the branch capacity.
    model.total_cost = pyo.Objective(
        expr=sum(
            model.edge_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi can raise when no feasible solution is available to load.
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solver_failed" if solver_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}
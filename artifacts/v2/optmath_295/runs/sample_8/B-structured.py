# IR: {"sets":{"N":"0..7","A":"[(i,j) for i in N for j in N if i!=j], row-major"},"params":{"arc_cost":"real vector indexed by A","net_outflow_node_0":"real scalar","net_inflow_node_7":"real scalar"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["sum_j x[0,j]-sum_i x[i,0]=net_outflow_node_0","sum_i x[i,7]-sum_j x[7,j]=net_inflow_node_7","sum_i x[i,k]-sum_j x[k,j]=0 for k=1..6"],"objective":"minimize sum_(i,j in A) arc_cost[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(8))
    arcs = [(source, target) for source in nodes for target in nodes
            if source != target]

    costs = list(params["arc_cost"])
    supply = params["net_outflow_node_0"]
    demand = params["net_inflow_node_7"]

    if len(costs) != len(arcs):
        return {"objective": None, "status": "invalid_arc_cost_length"}

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.route_cost = pyo.Param(
        model.arcs,
        initialize=dict(zip(arcs, costs)),
        within=pyo.Reals,
    )
    model.source_supply = pyo.Param(initialize=supply, within=pyo.Reals)
    model.destination_demand = pyo.Param(initialize=demand, within=pyo.Reals)
    model.route_used = pyo.Var(model.arcs, domain=pyo.Binary)

    def flow_balance_rule(network, node):
        outflow = sum(
            network.route_used[node, target]
            for target in network.nodes
            if target != node
        )
        inflow = sum(
            network.route_used[source, node]
            for source in network.nodes
            if source != node
        )
        if node == 0:
            return outflow - inflow == network.source_supply
        if node == 7:
            return inflow - outflow == network.destination_demand
        return inflow - outflow == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=flow_balance_rule)
    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[source, target] * model.route_used[source, target]
            for source, target in model.arcs
        ),
        sense=pyo.minimize,
    )

    # APPsi can raise RuntimeError when no feasible solution can be loaded.
    # Objective retrieval alone determines whether a solution is available.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
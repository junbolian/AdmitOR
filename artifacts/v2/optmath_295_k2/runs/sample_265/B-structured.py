# IR: {"sets":{"N":"0..7","A":"[(i,j) for i in N for j in N if i!=j], row-major"},"params":{"edge_cost":"cost vector indexed by A in row-major order","supply_node_0":"required net outflow at node 0","demand_node_7":"required net inflow at node 7"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["sum_j x[0,j]-sum_i x[i,0]=supply_node_0","sum_i x[i,7]-sum_j x[7,j]=demand_node_7","sum_j x[k,j]-sum_i x[i,k]=0 for k=1..6"],"objective":"minimize sum_(i,j in A) edge_cost[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(8))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    costs = params["edge_cost"]
    supply = params["supply_node_0"]
    demand = params["demand_node_7"]

    if len(costs) != len(arcs):
        raise ValueError("edge_cost must contain exactly 56 entries.")

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.route_cost = pyo.Param(
        model.arcs,
        initialize={arc: costs[position] for position, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.source_supply = pyo.Param(initialize=supply, within=pyo.Reals)
    model.sink_demand = pyo.Param(initialize=demand, within=pyo.Reals)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def balance_rule(instance, node):
        outgoing = sum(
            instance.x[node, other] for other in instance.nodes if other != node
        )
        incoming = sum(
            instance.x[other, node] for other in instance.nodes if other != node
        )
        if node == 0:
            return outgoing - incoming == instance.source_supply
        if node == 7:
            return incoming - outgoing == instance.sink_demand
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)
    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.x[i, j] for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
# IR: {"sets":{"N":"0..7","A":"[(i,j) for i in N for j in N if i!=j], row-major"},"params":{"edge_cost":"params['edge_cost'], indexed in A order","supply_node_0":"params['supply_node_0']","demand_node_7":"params['demand_node_7']"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["sum_j x[0,j]-sum_j x[j,0]=supply_node_0","sum_j x[7,j]-sum_j x[j,7]=-demand_node_7","sum_j x[i,j]-sum_j x[j,i]=0 for i=1..6"],"objective":"minimize sum_(i,j in A) edge_cost[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(8))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    edge_cost = params["edge_cost"]
    supply = params["supply_node_0"]
    demand = params["demand_node_7"]

    if len(edge_cost) != len(arcs):
        raise ValueError("edge_cost must contain 56 row-major entries.")

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.route_cost = pyo.Param(
        model.arcs,
        initialize={arc: edge_cost[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.source_supply = pyo.Param(initialize=supply, within=pyo.Reals)
    model.destination_demand = pyo.Param(initialize=demand, within=pyo.Reals)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def balance_rule(instance, i):
        outgoing = sum(instance.x[i, j] for j in instance.nodes if j != i)
        incoming = sum(instance.x[j, i] for j in instance.nodes if j != i)
        if i == 0:
            return outgoing - incoming == instance.source_supply
        if i == 7:
            return outgoing - incoming == -instance.destination_demand
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
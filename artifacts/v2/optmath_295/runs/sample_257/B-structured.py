# IR: {"sets":{"N":"0..7","A":"[(i,j) for i in N for j in N if i!=j], in lexicographic order"},"params":{"supply_node0":"params['supply_node0']","demand_node7":"params['demand_node7']","route_costs":"params['route_costs'], indexed by A order"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["sum_j x[0,j]-sum_i x[i,0]=supply_node0","sum_i x[i,7]-sum_j x[7,j]=demand_node7","sum_j x[k,j]-sum_i x[i,k]=0 for k in N excluding 0 and 7"],"objective":"minimize sum_(i,j in A) route_costs[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(8))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    supply = params["supply_node0"]
    demand = params["demand_node7"]
    route_costs = list(params["route_costs"])

    if len(route_costs) != len(arcs):
        raise ValueError("route_costs must contain exactly 56 entries.")

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.supply_node0 = pyo.Param(initialize=supply, within=pyo.Reals)
    model.demand_node7 = pyo.Param(initialize=demand, within=pyo.Reals)
    model.route_cost = pyo.Param(
        model.arcs,
        initialize=dict(zip(arcs, route_costs)),
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def flow_balance_rule(mod, node):
        outgoing = sum(mod.x[node, j] for j in mod.nodes if j != node)
        incoming = sum(mod.x[i, node] for i in mod.nodes if i != node)

        if node == 0:
            return outgoing - incoming == mod.supply_node0
        if node == 7:
            return incoming - outgoing == mod.demand_node7
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=flow_balance_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
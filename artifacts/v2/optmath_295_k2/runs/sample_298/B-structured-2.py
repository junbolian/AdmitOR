# IR: {"sets":{"N":"0..9","A":"(i,j), i!=j, whose cost_node{i}_to_node{j} key is provided; all listed origin-0 and origin-1 costs are required"},"params":{"supply":"scalar(params['supply_node0'])","demand":"scalar(params['demand_node9'])","intermediate":"scalar(params['intermediate_net_flow'])","cost[i,j]":"scalar(params['cost_node{i}_to_node{j}'])","scalar":"recursively unwrap singleton lists/tuples, then convert to float"},"variables":{"flow[i,j]":"binary for (i,j) in A"},"constraints":["outflow(0)-inflow(0)=supply","inflow(9)-outflow(9)=demand","outflow(k)-inflow(k)=intermediate for k=1..8"],"objective":"minimize sum_{(i,j) in A} cost[i,j]*flow[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _scalar(value):
    """Accept numeric values or numeric values wrapped in singleton sequences."""
    while isinstance(value, (list, tuple)):
        if len(value) != 1:
            raise ValueError("Expected a numeric scalar or a singleton sequence.")
        value = value[0]
    return float(value)


def solve(params):
    nodes = tuple(range(10))

    supply = _scalar(params["supply_node0"])
    demand = _scalar(params["demand_node9"])
    intermediate = _scalar(params["intermediate_net_flow"])

    # Every explicitly listed transportation-cost parameter is required.
    arc_costs = {
        (origin, destination): _scalar(
            params[f"cost_node{origin}_to_node{destination}"]
        )
        for origin in (0, 1)
        for destination in nodes
        if origin != destination
    }

    # Include additional priced arcs if supplied; never invent missing costs.
    for origin in range(2, 10):
        for destination in nodes:
            if origin != destination:
                key = f"cost_node{origin}_to_node{destination}"
                if key in params:
                    arc_costs[origin, destination] = _scalar(params[key])

    outgoing = {
        node: tuple(arc for arc in arc_costs if arc[0] == node)
        for node in nodes
    }
    incoming = {
        node: tuple(arc for arc in arc_costs if arc[1] == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(
        dimen=2, initialize=tuple(arc_costs), ordered=True
    )
    model.supply = pyo.Param(initialize=supply, within=pyo.Reals)
    model.demand = pyo.Param(initialize=demand, within=pyo.Reals)
    model.intermediate = pyo.Param(initialize=intermediate, within=pyo.Reals)
    model.cost = pyo.Param(
        model.arcs, initialize=arc_costs, within=pyo.Reals
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.Binary)

    def balance_rule(instance, node):
        net_outflow = (
            pyo.quicksum(instance.flow[arc] for arc in outgoing[node])
            - pyo.quicksum(instance.flow[arc] for arc in incoming[node])
        )
        if node == 0:
            required = instance.supply
        elif node == 9:
            required = -instance.demand
        else:
            required = instance.intermediate
        return (required, net_outflow, required)

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)
    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.cost[arc] * model.flow[arc] for arc in model.arcs
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
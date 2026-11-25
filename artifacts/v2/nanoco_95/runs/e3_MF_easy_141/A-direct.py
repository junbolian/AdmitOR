import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    costs = params["costs"]

    arcs = [
        (0, 1), (1, 2), (1, 7), (2, 3), (2, 6),
        (3, 4), (3, 8), (3, 9), (4, 5), (4, 8),
        (5, 6), (6, 7), (7, 8), (7, 9), (8, 9),
    ]
    nodes = list(range(10))
    source = 0
    sink = 9

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.nodes = pyo.Set(initialize=nodes)

    cap_dict = {a: capacities[i] for i, a in enumerate(arcs)}
    cost_dict = {a: costs[i] for i, a in enumerate(arcs)}

    model.cap = pyo.Param(model.arcs, initialize=cap_dict)
    model.cost = pyo.Param(model.arcs, initialize=cost_dict)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def cap_rule(m, i, j):
        return m.flow[i, j] <= m.cap[i, j]
    model.cap_con = pyo.Constraint(model.arcs, rule=cap_rule)

    def cons_rule(m, n):
        if n == source or n == sink:
            return pyo.Constraint.Skip
        inflow = sum(m.flow[i, j] for (i, j) in arcs if j == n)
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == n)
        return inflow == outflow
    model.cons_con = pyo.Constraint(model.nodes, rule=cons_rule)

    # Auxiliary variable for the total delivered flow (equals net outflow at source)
    model.total_flow = pyo.Var(domain=pyo.NonNegativeReals)

    def total_rule(m):
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == source)
        return m.total_flow == outflow
    model.total_con = pyo.Constraint(rule=total_rule)

    # Level-1 objective: maximize delivered flow
    model.max_flow_obj = pyo.Objective(expr=model.total_flow, sense=pyo.maximize)

    Highs().solve(model)
    max_flow_val = float(pyo.value(model.total_flow))

    # Fix delivered flow to the max, then minimize cost
    model.max_flow_obj.deactivate()
    model.total_con.deactivate()
    model.flow_fix = pyo.Constraint(expr=model.total_flow == max_flow_val)

    def cost_rule(m):
        return sum(m.cost[i, j] * m.flow[i, j] for (i, j) in arcs)
    model.cost_expr = pyo.Expression(rule=cost_rule)

    model.min_cost_obj = pyo.Objective(expr=model.cost_expr, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.min_cost_obj))

    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(7))
    arcs = [
        (0,1),(1,0),(0,2),(2,0),(0,3),(3,0),(0,4),(4,0),(0,5),(5,0),(0,6),(6,0),
        (1,2),(2,1),(1,3),(3,1),(1,4),(4,1),(1,5),(5,1),(1,6),(6,1),
        (2,3),(3,2),(2,4),(4,2),(2,5),(5,2),(2,6),(6,2),
        (3,4),(4,3),(3,5),(5,3),(3,6),(6,3),
        (4,5),(5,4),(4,6),(6,4),
        (5,6),(6,5)
    ]

    net_outflow = params["node_net_outflow"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]

    fc = {a: fixed_cost[i] for i, a in enumerate(arcs)}
    vc = {a: variable_cost[i] for i, a in enumerate(arcs)}
    cap = {a: capacity[i] for i, a in enumerate(arcs)}

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes)
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.ARCS, domain=pyo.Binary)

    def flow_rule(model, i):
        out_flow = sum(model.x[i, j] for (a, b) in arcs if a == i for j in [b])
        in_flow = sum(model.x[j, i] for (a, b) in arcs if b == i for j in [a])
        return out_flow - in_flow == net_outflow[i]

    model.flow_con = pyo.Constraint(model.NODES, rule=flow_rule)

    def cap_rule(model, a, b):
        return model.x[a, b] <= cap[(a, b)] * model.y[a, b]

    model.cap_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    def obj_rule(model):
        return sum(fc[a] * model.y[a] + vc[a] * model.x[a] for a in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
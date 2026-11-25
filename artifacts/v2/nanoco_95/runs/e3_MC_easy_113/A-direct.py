import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    capacities = list(params["arc_capacities"])
    
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 7),
        (1, 2), (1, 5),
        (2, 3), (2, 5), (2, 6),
        (3, 4), (3, 5),
        (4, 5), (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]
    num_nodes = 8
    nodes = list(range(num_nodes))
    
    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(initialize=list(range(len(arcs))))
    
    # x[n] = 1 if node in S (source side), 0 if in T (sink side)
    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    
    model.arc_from = {k: arcs[k][0] for k in range(len(arcs))}
    model.arc_to = {k: arcs[k][1] for k in range(len(arcs))}
    
    # Fix source in S, sink in T
    model.source_fix = pyo.Constraint(expr=model.x[0] == 1)
    model.sink_fix = pyo.Constraint(expr=model.x[7] == 0)
    
    # y[k] = 1 if arc k crosses from S to T
    model.y = pyo.Var(model.arcs, domain=pyo.Binary)
    
    def cap_rule(m, k):
        i = m.arc_from[k]
        j = m.arc_to[k]
        return m.y[k] >= m.x[i] - m.x[j]
    model.cut_def = pyo.Constraint(model.arcs, rule=cap_rule)
    
    def obj_rule(m):
        return sum(capacities[k] * m.y[k] for k in m.arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    
    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
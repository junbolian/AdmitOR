import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    model = pyo.ConcreteModel()
    
    arcs = [
        (0,1),(0,2),(0,3),(0,4),(0,5),
        (1,0),(1,2),(1,4),(1,5),
        (2,0),(2,1),(2,3),(2,4),(2,5),
        (3,0),(3,1),(3,2),(3,4),(3,5),
        (4,0),(4,1),(4,2),(4,3),(4,5),
        (5,0),(5,1),(5,2),(5,3),(5,4),
    ]
    
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    
    cap = {}
    for (i, j) in arcs:
        cap[(i, j)] = params["capacity_%d_%d" % (i, j)]
    
    def arc_bound(mdl, i, j):
        return mdl.flow[i, j] <= cap[(i, j)]
    model.cap_cons = pyo.Constraint(model.arcs, rule=arc_bound)
    
    src = 0
    dst = 5
    nodes = [0, 1, 2, 3, 4, 5]
    
    def flow_balance(mdl, n):
        outflow = sum(mdl.flow[n, j] for (i, j) in arcs if i == n)
        inflow = sum(mdl.flow[i, n] for (i, j) in arcs if j == n)
        if n == src:
            return outflow - inflow >= 0
        elif n == dst:
            return inflow - outflow >= 0
        else:
            return outflow - inflow == 0
    model.balance = pyo.Constraint(nodes, rule=flow_balance)
    
    def net_out(mdl):
        return sum(mdl.flow[src, j] for (i, j) in arcs if i == src) - sum(mdl.flow[i, src] for (i, j) in arcs if j == src)
    model.obj_expr = pyo.Expression(rule=net_out)
    
    model.maxflow = pyo.Objective(rule=net_out, sense=pyo.maximize)
    
    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.maxflow))
        return {'objective': obj_val, 'status': 'optimal'}
    except Exception:
        return {'objective': None, 'status': 'infeasible_or_failed'}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    num_users = len(params["latency"])
    num_locations = len(params["fixed_cost"])
    
    model = pyo.ConcreteModel()
    
    model.Users = pyo.Set(initialize=range(num_users))
    model.Locations = pyo.Set(initialize=range(num_locations))
    
    model.fixed_cost = pyo.Param(
        model.Locations,
        initialize={l: params["fixed_cost"][l] for l in range(num_locations)}
    )
    model.latency = pyo.Param(
        model.Users,
        model.Locations,
        initialize={(u, l): params["latency"][u][l]
                    for u in range(num_users) for l in range(num_locations)}
    )
    
    model.y = pyo.Var(model.Locations, within=pyo.Binary)
    model.x = pyo.Var(model.Users, model.Locations, within=pyo.Binary)
    
    def obj_rule(m):
        return (sum(m.fixed_cost[l] * m.y[l] for l in m.Locations) +
                sum(m.latency[u, l] * m.x[u, l] for u in m.Users for l in m.Locations))
    
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    
    def assign_rule(m, u):
        return sum(m.x[u, l] for l in m.Locations) == 1
    
    model.assign_constraint = pyo.Constraint(model.Users, rule=assign_rule)
    
    def link_rule(m, u, l):
        return m.x[u, l] <= m.y[l]
    
    model.link_constraint = pyo.Constraint(model.Users, model.Locations, rule=link_rule)
    
    solver = Highs()
    solver.config.stream_solver = False
    solver.solve(model)
    
    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible"}
    
    return {"objective": obj_val, "status": "optimal"}
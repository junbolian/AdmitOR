import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    rack_power_capacity = params["rack_power_capacity"]
    rack_cooling_capacity = params["rack_cooling_capacity"]
    server_power_demand = params["server_power_demand"]
    server_cooling_demand = params["server_cooling_demand"]

    num_servers = len(server_power_demand)
    servers = list(range(num_servers))
    racks = list(range(num_servers))

    model = pyo.ConcreteModel()

    model.SERVERS = pyo.Set(initialize=servers, ordered=True)
    model.RACKS = pyo.Set(initialize=racks, ordered=True)

    model.assign = pyo.Var(model.SERVERS, model.RACKS, domain=pyo.Binary)
    model.use_rack = pyo.Var(model.RACKS, domain=pyo.Binary)

    def assign_once_rule(m, s):
        return sum(m.assign[s, r] for r in m.RACKS) == 1

    model.assign_once = pyo.Constraint(model.SERVERS, rule=assign_once_rule)

    def link_rule(m, s, r):
        return m.assign[s, r] <= m.use_rack[r]

    model.link = pyo.Constraint(model.SERVERS, model.RACKS, rule=link_rule)

    def power_rule(m, r):
        return sum(server_power_demand[s] * m.assign[s, r] for s in m.SERVERS) <= rack_power_capacity

    model.power_cap = pyo.Constraint(model.RACKS, rule=power_rule)

    def cooling_rule(m, r):
        return sum(server_cooling_demand[s] * m.assign[s, r] for s in m.SERVERS) <= rack_cooling_capacity

    model.cooling_cap = pyo.Constraint(model.RACKS, rule=cooling_rule)

    def symmetry_rule(m, r):
        if r == 0:
            return pyo.Constraint.Skip
        return m.use_rack[r] <= m.use_rack[r - 1]

    model.symmetry = pyo.Constraint(model.RACKS, rule=symmetry_rule)

    def obj_rule(m):
        return sum(m.use_rack[r] for r in m.RACKS)

    model.total_racks = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_racks))
    return {"objective": obj_val, "status": "optimal"}
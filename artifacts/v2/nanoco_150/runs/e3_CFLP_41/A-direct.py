import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    station_x = params["station_x"]
    station_y = params["station_y"]
    vehicle_x = params["vehicle_x"]
    vehicle_y = params["vehicle_y"]
    installation_cost = params["installation_cost"]
    station_capacity = params["station_capacity"]
    vehicle_demand = params["vehicle_demand"]
    access_cost = params["access_cost"]
    num_stations = params["num_stations"]
    num_vehicles = params["num_vehicles"]

    stations = list(range(num_stations))
    vehicles = list(range(num_vehicles))

    model = pyo.ConcreteModel()

    model.S = pyo.Set(initialize=stations, ordered=True)
    model.V = pyo.Set(initialize=vehicles, ordered=True)

    model.build = pyo.Var(model.S, domain=pyo.Binary)
    model.assign = pyo.Var(model.V, model.S, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(installation_cost[s] * mdl.build[s] for s in mdl.S) + \
               sum(access_cost[v][s] * mdl.assign[v, s] for v in mdl.V for s in mdl.S)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def single_source_rule(mdl, v):
        return sum(mdl.assign[v, s] for s in mdl.S) == 1

    model.single_source = pyo.Constraint(model.V, rule=single_source_rule)

    def capacity_rule(mdl, s):
        return sum(vehicle_demand[v] * mdl.assign[v, s] for v in mdl.V) <= \
               station_capacity[s] * mdl.build[s]

    model.capacity = pyo.Constraint(model.S, rule=capacity_rule)

    def link_rule(mdl, v, s):
        return mdl.assign[v, s] <= mdl.build[s]

    model.link = pyo.Constraint(model.V, model.S, rule=link_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_plane0 = params["cost_plane0"]
    cost_plane1 = params["cost_plane1"]
    demand_0to1 = params["demand_0to1"]
    capacity_plane0 = params["capacity_plane0"]
    capacity_plane1 = params["capacity_plane1"]
    fleet_plane0 = params["fleet_plane0"]
    fleet_plane1 = params["fleet_plane1"]
    max_trips_plane0 = params["max_trips_plane0"]
    max_trips_plane1 = params["max_trips_plane1"]

    model = pyo.ConcreteModel()

    # Decision variables: trips from 0->1 for each plane type
    model.trips_0to1_plane0 = pyo.Var(domain=pyo.NonNegativeIntegers,
                                      bounds=(0, max_trips_plane0))
    model.trips_0to1_plane1 = pyo.Var(domain=pyo.NonNegativeIntegers,
                                      bounds=(0, max_trips_plane1))

    # Demand satisfaction
    def demand_rule(m):
        return (capacity_plane0 * m.trips_0to1_plane0
                + capacity_plane1 * m.trips_0to1_plane1) >= demand_0to1
    model.demand_con = pyo.Constraint(rule=demand_rule)

    # Fleet availability constraints
    def fleet_rule0(m):
        return m.trips_0to1_plane0 <= fleet_plane0
    model.fleet_con0 = pyo.Constraint(rule=fleet_rule0)

    def fleet_rule1(m):
        return m.trips_0to1_plane1 <= fleet_plane1
    model.fleet_con1 = pyo.Constraint(rule=fleet_rule1)

    # Objective: minimize total cost
    def obj_rule(m):
        return (cost_plane0 * m.trips_0to1_plane0
                + cost_plane1 * m.trips_0to1_plane1)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
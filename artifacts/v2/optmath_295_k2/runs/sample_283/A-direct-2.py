import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    revenue = params["revenue"]
    demand_limit = params["demand_limit"]
    route_capacity = params["route_capacity"]

    n = len(revenue)
    m = len(route_capacity)

    route_packages = [
        [0,1,2,3,4,5,6,7,8,10,11,12,15,16,17,18,19,20,21],
        [1,2,4,5,6,8,9,10,11,12,14,15,16,17,18,19,22],
        [2,3,4,8,9,11,12,13,15,17,18,20,21],
        [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,19,20,21,22],
        [1,3,4,5,7,8,9,10,13,14,15,17,18,20,21,22],
        [0,1,2,4,5,6,8,9,10,11,12,13,16,17,18,20,21,22],
        [0,1,2,3,4,5,6,8,9,13,15,16,17,18,19,21,22],
        [0,1,2,5,7,8,10,12,14,16,19,20,21,22],
        [2,3,4,5,6,7,9,10,12,13,14,15,16,17,18,19,20,21,22],
        [0,1,5,6,7,8,9,10,13,14,15,17,18,19,20],
        [0,1,2,3,4,6,8,9,10,12,13,14,15,16,17,22],
        [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,18,19,20,21],
        [0,1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22],
        [0,1,2,6,7,8,10,11,13,15,16,17,18,19,20,22],
        [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,17,18,19,20,21,22],
    ]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n - 1)
    model.R = pyo.RangeSet(0, m - 1)

    model.x = pyo.Var(model.P, within=pyo.NonNegativeIntegers)

    def demand_rule(mdl, i):
        return mdl.x[i] <= demand_limit[i]
    model.demand_con = pyo.Constraint(model.P, rule=demand_rule)

    def route_rule(mdl, r):
        return sum(mdl.x[i] for i in route_packages[r]) <= route_capacity[r]
    model.route_con = pyo.Constraint(model.R, rule=route_rule)

    def obj_rule(mdl):
        return sum(revenue[i] * mdl.x[i] for i in mdl.P)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}
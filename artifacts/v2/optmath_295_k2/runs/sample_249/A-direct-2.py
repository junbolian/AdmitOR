import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [0, 1, 2, 3]
    products = [0, 1]
    pairs = [(i, j) for i in cities for j in cities if i != j]
    param_city_names = {
        0: "city0", 1: "city1", 2: "city2", 3: "city3"
    }

    transport_cost = params["transport_cost_per_unit"]
    joint_cap = params["joint_capacity_per_pair"]

    net_flow = {}
    for c in cities:
        for p in products:
            net_flow[(c, p)] = params[
                "net_flow_{}_product{}".format(param_city_names[c], p)
            ]

    prod_cap = {}
    for (i, j) in pairs:
        for p in products:
            prod_cap[(i, j, p)] = params[
                "product{}_capacity_{}_{}".format(
                    p, param_city_names[i], param_city_names[j]
                )
            ]

    model = pyo.ConcreteModel()

    model.PAIRS = pyo.Set(initialize=pairs, dimen=2)
    model.PRODUCTS = pyo.Set(initialize=products)
    model.CITIES = pyo.Set(initialize=cities)
    model.CITY_PRODUCT = pyo.Set(initialize=[(c, p) for c in cities for p in products], dimen=2)
    model.PAIR_PRODUCT = pyo.Set(initialize=[(i, j, p) for (i, j) in pairs for p in products], dimen=3)

    model.x = pyo.Var(model.PAIR_PRODUCT, domain=pyo.NonNegativeReals)

    def flow_balance_rule(mdl, c, p):
        outflow = sum(mdl.x[(c, j, p)] for j in cities if j != c)
        inflow = sum(mdl.x[(i, c, p)] for i in cities if i != c)
        return inflow - outflow == net_flow[(c, p)]

    model.flow_con = pyo.Constraint(model.CITY_PRODUCT, rule=flow_balance_rule)

    def joint_cap_rule(mdl, i, j):
        return sum(mdl.x[(i, j, p)] for p in products) <= joint_cap

    model.joint_con = pyo.Constraint(model.PAIRS, rule=joint_cap_rule)

    def prod_cap_rule(mdl, i, j, p):
        return mdl.x[(i, j, p)] <= prod_cap[(i, j, p)]

    model.prod_con = pyo.Constraint(model.PAIR_PRODUCT, rule=prod_cap_rule)

    def obj_rule(mdl):
        return sum(transport_cost * mdl.x[(i, j, p)] for (i, j) in pairs for p in products)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 5
    feeds = list(range(n))

    model = pyo.ConcreteModel()

    def p_content(f):
        return params["protein_content"][f]

    def m_content(f):
        return params["minerals_content"][f]

    def v_content(f):
        return params["vitamins_content"][f]

    def cost_kg(f):
        return params["price"][f]

    model.x = pyo.Var(feeds, domain=pyo.NonNegativeReals)

    def protein_rule(model):
        return sum(p_content(f) * model.x[f] for f in feeds) >= params["requirement_protein"]

    def minerals_rule(model):
        return sum(m_content(f) * model.x[f] for f in feeds) >= params["requirement_minerals"]

    def vitamins_rule(model):
        return sum(v_content(f) * model.x[f] for f in feeds) >= params["requirement_vitamins"]

    model.protein_con = pyo.Constraint(rule=protein_rule)
    model.minerals_con = pyo.Constraint(rule=minerals_rule)
    model.vitamins_con = pyo.Constraint(rule=vitamins_rule)

    def obj_rule(model):
        return sum(cost_kg(f) * model.x[f] for f in feeds)

    model.cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}
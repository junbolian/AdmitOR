import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    proteins = ["chicken", "salmon", "tofu", "broccoli", "carrots", "spinach", "bell_pepper", "mushrooms"]
    continuous = ["chicken", "salmon", "tofu"]
    vegetables = ["broccoli", "carrots", "spinach", "bell_pepper", "mushrooms"]

    model = pyo.ConcreteModel()

    # Continuous quantities (in 100g units) for protein options
    model.x = pyo.Var(continuous, domain=pyo.NonNegativeReals)
    # Binary selection for vegetables
    model.y = pyo.Var(vegetables, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.x[i] * params["protein_" + i] for i in continuous) + \
               sum(m.y[j] * params["protein_" + j] for j in vegetables)
    model.total_protein = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def budget_rule(m):
        return sum(m.x[i] * params["cost_" + i] for i in continuous) + \
               sum(m.y[j] * params["cost_" + j] for j in vegetables) <= params["budget"]
    model.budget_con = pyo.Constraint(rule=budget_rule)

    def weight_rule(m):
        return 100 * (sum(m.x[i] for i in continuous) + sum(m.y[j] for j in vegetables)) <= params["max_weight"]
    model.weight_con = pyo.Constraint(rule=weight_rule)

    def veg_min_rule(m):
        return sum(m.y[j] for j in vegetables) >= params["min_vegetable_types"]
    model.veg_min_con = pyo.Constraint(rule=veg_min_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_protein))
    return {'objective': obj_val, 'status': 'optimal'}
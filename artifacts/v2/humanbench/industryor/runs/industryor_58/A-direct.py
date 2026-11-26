import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    protein_requirement = params["protein_requirement"]
    mineral_requirement = params["mineral_requirement"]
    vitamin_requirement = params["vitamin_requirement"]
    protein_content = params["protein_content"]
    mineral_content = params["mineral_content"]
    vitamin_content = params["vitamin_content"]
    feed_price = params["feed_price"]

    feeds = list(range(5))

    model = pyo.ConcreteModel()

    # Decision: grams of each feed selected per day
    model.feed_amount = pyo.Var(feeds, domain=pyo.NonNegativeReals)

    # Objective: minimize cost. Price is yuan/kg, so convert to yuan/g (divide by 1000)
    def cost_rule(m):
        return sum(feed_price[i] / 1000.0 * m.feed_amount[i] for i in feeds)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    # Constraints
    def protein_rule(m):
        return sum(protein_content[i] * m.feed_amount[i] for i in feeds) >= protein_requirement
    model.protein_con = pyo.Constraint(rule=protein_rule)

    def mineral_rule(m):
        return sum(mineral_content[i] * m.feed_amount[i] for i in feeds) >= mineral_requirement
    model.mineral_con = pyo.Constraint(rule=mineral_rule)

    def vitamin_rule(m):
        return sum(vitamin_content[i] * m.feed_amount[i] for i in feeds) >= vitamin_requirement
    model.vitamin_con = pyo.Constraint(rule=vitamin_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
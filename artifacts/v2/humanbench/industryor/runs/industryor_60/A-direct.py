import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_I = params["supply_I"]
    supply_I_prime = params["supply_I_prime"]
    supply_II = params["supply_II"]
    cost_I = params["cost_I"]
    cost_I_prime = params["cost_I_prime"]
    cost_II = params["cost_II"]
    price_red = params["price_red"]
    price_yellow = params["price_yellow"]
    price_blue = params["price_blue"]
    red_min_output = params["red_min_output"]
    red_gradeI_upper_frac = params["red_gradeI_upper_frac"]
    red_gradeI_lower_frac = params["red_gradeI_lower_frac"]
    yellow_gradeII_upper_frac = params["yellow_gradeII_upper_frac"]
    yellow_gradeI_lower_frac = params["yellow_gradeI_lower_frac"]
    blue_gradeI_upper_frac = params["blue_gradeI_upper_frac"]
    blue_gradeI_lower_frac = params["blue_gradeI_lower_frac"]

    grades = ['I', 'Ip', 'II']
    brands = ['red', 'yellow', 'blue']
    pairs = [(g, b) for g in grades for b in brands]

    model = pyo.ConcreteModel()

    # x[g, b] = amount of grade g used in brand b (kg/day)
    model.x = pyo.Var(pairs, domain=pyo.NonNegativeReals)

    # Supply constraints
    model.supply_I_c = pyo.Constraint(
        expr=model.x['I', 'red'] + model.x['I', 'yellow'] + model.x['I', 'blue'] <= supply_I
    )
    model.supply_Ip_c = pyo.Constraint(
        expr=model.x['Ip', 'red'] + model.x['Ip', 'yellow'] + model.x['Ip', 'blue'] <= supply_I_prime
    )
    model.supply_II_c = pyo.Constraint(
        expr=model.x['II', 'red'] + model.x['II', 'yellow'] + model.x['II', 'blue'] <= supply_II
    )

    # Red brand: first grade-I row fraction upper bound
    model.red_upper_c = pyo.Constraint(
        expr=model.x['I', 'red']
        <= red_gradeI_upper_frac * (model.x['I', 'red'] + model.x['Ip', 'red'] + model.x['II', 'red'])
    )
    # Red brand: lower bound on grade I fraction
    model.red_lower_c = pyo.Constraint(
        expr=model.x['I', 'red']
        >= red_gradeI_lower_frac * (model.x['I', 'red'] + model.x['Ip', 'red'] + model.x['II', 'red'])
    )
    # Red brand minimum output
    model.red_min_c = pyo.Constraint(
        expr=model.x['I', 'red'] + model.x['Ip', 'red'] + model.x['II', 'red'] >= red_min_output
    )

    # Yellow brand: II fraction upper bound
    model.yellow_upper_c = pyo.Constraint(
        expr=model.x['II', 'yellow']
        <= yellow_gradeII_upper_frac * (model.x['I', 'yellow'] + model.x['Ip', 'yellow'] + model.x['II', 'yellow'])
    )
    # Yellow brand: grade I fraction lower bound
    model.yellow_lower_c = pyo.Constraint(
        expr=model.x['I', 'yellow']
        >= yellow_gradeI_lower_frac * (model.x['I', 'yellow'] + model.x['Ip', 'yellow'] + model.x['II', 'yellow'])
    )

    # Blue brand: grade I fraction upper bound
    model.blue_upper_c = pyo.Constraint(
        expr=model.x['I', 'blue']
        <= blue_gradeI_upper_frac * (model.x['I', 'blue'] + model.x['Ip', 'blue'] + model.x['II', 'blue'])
    )
    # Blue brand: grade I fraction lower bound
    model.blue_lower_c = pyo.Constraint(
        expr=model.x['I', 'blue']
        >= blue_gradeI_lower_frac * (model.x['I', 'blue'] + model.x['Ip', 'blue'] + model.x['II', 'blue'])
    )

    # objective components
    model.red_total_v = pyo.Expression(
        expr=model.x['I', 'red'] + model.x['Ip', 'red'] + model.x['II', 'red']
    )
    model.yellow_total_v = pyo.Expression(
        expr=model.x['I', 'yellow'] + model.x['Ip', 'yellow'] + model.x['II', 'yellow']
    )
    model.blue_total_v = pyo.Expression(
        expr=model.x['I', 'blue'] + model.x['Ip', 'blue'] + model.x['II', 'blue']
    )

    revenue = (
        price_red * model.red_total_v
        + price_yellow * model.yellow_total_v
        + price_blue * model.blue_total_v
    )
    cost = (
        cost_I * (model.x['I', 'red'] + model.x['I', 'yellow'] + model.x['I', 'blue'])
        + cost_I_prime * (model.x['Ip', 'red'] + model.x['Ip', 'yellow'] + model.x['Ip', 'blue'])
        + cost_II * (model.x['II', 'red'] + model.x['II', 'yellow'] + model.x['II', 'blue'])
    )
    model.obj = pyo.Objective(expr=revenue - cost, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}
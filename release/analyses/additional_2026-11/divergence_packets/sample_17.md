# sample_17

Decision: ACCEPT, clique ['A-direct', 'C-direct'], informative [0, 1, 2, 3, 4, 5], label 9.0

## Problem text

Minimize the total number of rolls cut across all patterns while meeting customer orders for four different widths: Width 1 requires at least 34 units, Width 2 requires at least 25 units, Width 3 requires at least 21 units, and Width 4 requires at least 27 units. There are 12 cutting patterns available, each specifying how rolls of varying widths can be produced. The patterns are as follows: Pattern 0 produces 3 units of Width 1, 2 units of Width 2, and 4 units of Width 4; Pattern 1 produces 5 units of Width 1, 3 units of Width 2, and 1 unit of Width 4; Pattern 2 produces 1 unit of Width 3 and 4 units of Width 4; Pattern 3 produces 2 units of Width 1, 4 units of Width 2, 4 units of Width 3, and 3 units of Width 4; Pattern 4 produces 4 units of Width 3 and 4 units of Width 4; Pattern 5 produces 2 units of Width 1, 1 unit of Width 2, 1 unit of Width 3, and 1 unit of Width 4; Pattern 6 produces 1 unit of Width 1, 4 units of Width 2, 1 unit of Width 3, and 5 units of Width 4; Pattern 7 produces 1 unit of Width 1, 1 unit of Width 2, and 1 unit of Width 4; Pattern 8 produces 3 units of Width 1, 3 units of Width 2, 5 units of Width 3, and 5 units of Width 4; Pattern 9 produces 2 units of Width 1, 4 units of Width 2, 2 units of Width 3, and 5 units of Width 4; Pattern 10 produces 4 units of Width 2, 5 units of Width 3, and 2 units of Width 4; Pattern 11 produces 4 units of Width 2 and 4 units of Width 3. Each pattern has a usage limit: Pattern 0 can be used up to 42 times, Pattern 1 up to 45 times, Pattern 2 up to 53 times, Pattern 3 up to 21 times, Pattern 4 up to 37 times, Pattern 5 up to 69 times, Pattern 6 up to 23 times, Pattern 7 up to 68 times, Pattern 8 up to 11 times, Pattern 9 up to 39 times, Pattern 10 up to 49 times, and Pattern 11 up to 50 times. The number of times each pattern is used must be a whole number. The objective is to minimize the total number of rolls cut while ensuring all customer orders are met and the usage limits for each pattern are respected.

## Values and statuses per instance

| Candidate | inst 0 | inst 1 | inst 2 | inst 3 | inst 4 | inst 5 |
|---|---|---|---|---|---|---|
| A-direct | 9.0 (optimal) | 9.0 (optimal) | 11.0 (optimal) | 12.0 (optimal) | 10.0 (optimal) | 9.0 (optimal) |
| B-structured | 9.0 (optimal) | None (crash:raise ValueError( ) | None (crash:raise ValueError( ) | None (crash:raise ValueError( ) | None (crash:raise ValueError( ) | None (crash:raise ValueError( ) |
| C-direct | 9.0 (optimal) | 9.0 (optimal) | 11.0 (optimal) | 12.0 (optimal) | 10.0 (optimal) | 9.0 (optimal) |

## Sampled parameters per instance

instance 0: `{"demands": [34, 25, 21, 27], "pattern_limits": [42, 45, 53, 21, 37, 69, 23, 68, 11, 39, 49, 50], "pattern_yields": [[3, 2, 0, 4], [5, 3, 0, 1], [0, 0, 1, 4], [2, 4, 4, 3], [0, 0, 4, 4], [2, 1, 1, 1], [1, 4, 1, 5], [1, 1, 0, 1], [3, 3, 5, 5], [2, 4, 2, 5], [0, 4, 5, 2], [0, 4, 4, 0]]}`
instance 1: `{"demands": [36.844306688540826, 17.875161328340003, 18.1653694114509, 22.516013958010927], "pattern_limits": [47.959074596933114, 49.77088616041861, 65.47131025301408, 15.795429291130644, 35.266664397013, 49.533604884736114, 19.117204052289726, 68.2184957546172, 7.8751373999135, 31.952801026067572, 53.40660247071798, 51.3482444180965], "pattern_yields": [[2.496793119673254, 2.1071188206510905, 0.0, 2.815597023227346], [5.917457755498424, 3.356650910978808, 0.0, 0.7932876998870689], [0.0, 0.0, 0.7556475060280887, 3.0321193044003136], [2.416993239616952, 4.248942475280539, 4.737107855858513, 3.4135172160488723], [0.0, 0.0, 3.708482505300048, 4.1248975150557445], [2.395285597103594, 1.0711118514185476, 1.2170241401864663, 1.0464112871540572], [1.122743101728954, 2.9099785207735893, 0.8367389653909281, 4.368163890806321], [0.7478751861541765, 0.8396745318166181, 0.0, 0.8667841618660552], [3.24423199967592, 2.7566979221461514, 4.610542901350648, 4.128521092314463], [1.720373386458936, 5.047971010509986, 2.1776424622959123, 5.327393017000964], [0.0, 4.549904315080838, 3.9902074812857853, 1.8553465301091774], [0.0, 4.335999423649823, 4.136679385059151, 0.0]]}`
instance 2: `{"demands": [40.99417917187212, 29.139998673193674, 17.586005706747716, 19.420023951245412], "pattern_limits": [37.34941681108886, 38.72900365134397, 43.80925442604518, 26.580662400621684, 45.35536130769325, 61.32766426505698, 25.145053581069348, 63.7417815632751, 13.736014092287588, 38.03713335054513, 42.08747689504274, 42.398825230819504], "pattern_yields": [[3.1104626414936716, 1.7152899302275224, 0.0, 4.954774920645945], [4.698201515421192, 2.49477736648311, 0.0, 1.0057157762058786], [0.0, 0.0, 0.7657894782103954, 4.3058705000874165], [2.350495237235557, 3.8131839203192417, 2.952466494764697, 2.7869147157117657], [0.0, 0.0, 5.130588106272684, 4.865871285362795], [1.4137772263313835, 1.1324330916161167, 1.1090262214159448, 1.022182198245277], [0.8600951139715256, 4.338308316591539, 0.7669313041575259, 4.804295752007315], [0.9722342237975239, 1.2722895565126482, 0.0, 0.8580334304506545], [3.0010550034905368, 2.4215733849542365, 6.237883518034462, 6.111555709510301], [1.7581337497383593, 4.333478787678413, 2.1307642537258067, 3.9585178056489045], [0.0, 4.094509672287102, 5.835879435891675, 2.0364244066342128], [0.0, 3.5779745368112152, 2.8467441817259975, 0.0]]}`
instance 3: `{"demands": [41.72592630759296, 29.974982940417693, 18.574677980073535, 19.838387697205835], "pattern_limits": [51.52584189994182, 57.067635023045845, 39.823779775758545, 20.823479837789332, 27.436517909998113, 79.78892964164939, 26.668515124436432, 52.83837175159032, 10.836863695451626, 40.16540408778168, 42.09266489083774, 61.17299123255773], "pattern_yields": [[2.861648292361596, 1.6541578465304985, 0.0, 4.551834565815943], [4.103453190169088, 2.661089324341611, 0.0, 1.0899268345836721], [0.0, 0.0, 0.7726025175209594, 3.3392736088757378], [1.8057026745769464, 4.21194092429736, 3.352275358231785, 2.496391292012807], [0.0, 0.0, 3.3494602811467704, 4.973008031214707], [2.431562480304496, 0.7425144099331921, 0.8428027806213971, 1.1013866669777683], [0.8285420844222631, 3.11754843694006, 1.2613085443484027, 5.2131292799758535], [0.9836026157870765, 1.170771654574452, 0.0, 0.8142459486171266], [2.2744754656118817, 2.875892128331479, 4.770735869059762, 4.901074004110025], [2.274891019351821, 4.416074913503923, 2.5809982536391596, 3.795253613455877], [0.0, 3.6143262529479117, 6.085017609058374, 1.6983876007043426], [0.0, 3.8766725147995165, 3.81251593560257, 0.0]]}`
instance 4: `{"demands": [28.89605153679485, 31.348983989140194, 20.283447387673558, 32.85385549714166], "pattern_limits": [43.26819787373617, 32.86588489717179, 68.8771824955247, 25.233947572007395, 47.41171691172148, 86.65159309653649, 27.812001134917413, 54.38549331263969, 10.905231427974742, 32.30168680126085, 46.09058460095391, 36.75906199916537], "pattern_yields": [[2.782151614158449, 2.582370612535671, 0.0, 4.681769444676567], [4.865025102017429, 2.8614134747822932, 0.0, 1.2972536136956283], [0.0, 0.0, 0.7928780951644384, 3.512098781186954], [2.562451237962991, 4.1900326979590155, 4.101268483298258, 3.4463560086823155], [0.0, 0.0, 4.006840919006833, 4.846527740915885], [1.5889192735273798, 1.2764673419646702, 0.7480668791443521, 0.8114949765884338], [1.0570210638700166, 4.420510128649816, 0.8411223370005587, 3.8596598418413723], [1.2341723884776625, 0.8477292086731749, 0.0, 1.0716289061992619], [2.8546048476045707, 3.1506101207242048, 5.068348146595877, 6.304118773209282], [1.6451110393082438, 4.5188603218945955, 1.6864231431390153, 4.687357540373763], [0.0, 3.519992991517029, 4.448531588815562, 2.3022373908972824], [0.0, 3.899885254284607, 5.196290658050662, 0.0]]}`
instance 5: `{"demands": [25.29451871043251, 20.697314684005605, 18.041525225855054, 34.01880192349809], "pattern_limits": [51.59777717689828, 55.24029654708266, 48.850961421896514, 16.68761008770112, 44.40913799300372, 77.42655289861716, 24.541153167018113, 87.87910899616539, 12.016243696890836, 27.483060707360497, 58.32286157239457, 43.98136256599934], "pattern_yields": [[3.294099686938939, 2.526716004712525, 0.0, 3.0770288090058453], [3.8211079331282525, 3.0958025535926685, 0.0, 1.0628978962181344], [0.0, 0.0, 1.080542775331048, 3.4335613639129825], [1.9862382225792519, 4.972807578590376, 4.830648911907653, 2.26613724188292], [0.0, 0.0, 2.8085096538106775, 4.650686135247105], [2.1645360527616555, 0.857173157460609, 1.1447385450087584, 1.0310082526758348], [0.9566121513884076, 2.8232072790600156, 0.7451463160442602, 6.14931917990043], [1.242357142935936, 1.0273541735233134, 0.0, 1.0495057398938763], [2.3665688140214685, 2.3294019347078496, 4.424775049790401, 6.1969444662277695], [2.35534676586565, 4.865686196802167, 2.4787095638317695, 4.130229615019262], [0.0, 3.0467046920122853, 5.840348725614328, 2.4609616417412106], [0.0, 4.289587624361711, 3.170928011997291, 0.0]]}`

## Extracted specification

```json
{
 "demands": {
  "base": [
   34,
   25,
   21,
   27
  ],
  "perturb": {
   "mode": "rel",
   "r": 0.3
  }
 },
 "pattern_limits": {
  "base": [
   42,
   45,
   53,
   21,
   37,
   69,
   23,
   68,
   11,
   39,
   49,
   50
  ],
  "perturb": {
   "mode": "rel",
   "r": 0.3
  }
 },
 "pattern_yields": {
  "base": [
   [
    3,
    2,
    0,
    4
   ],
   [
    5,
    3,
    0,
    1
   ],
   [
    0,
    0,
    1,
    4
   ],
   [
    2,
    4,
    4,
    3
   ],
   [
    0,
    0,
    4,
    4
   ],
   [
    2,
    1,
    1,
    1
   ],
   [
    1,
    4,
    1,
    5
   ],
   [
    1,
    1,
    0,
    1
   ],
   [
    3,
    3,
    5,
    5
   ],
   [
    2,
    4,
    2,
    5
   ],
   [
    0,
    4,
    5,
    2
   ],
   [
    0,
    4,
    4,
    0
   ]
  ],
  "perturb": {
   "mode": "rel",
   "r": 0.3
  }
 }
}
```

## Program A-direct

```python
import pyomo.environ as pyo

def solve(params):
    # Extract data from params dict
    demands = params["demands"]  # list of 4 integers
    pattern_limits = params["pattern_limits"]  # list of 12 integers
    pattern_yields = params["pattern_yields"]  # 12×4 list of integers

    # Create model
    model = pyo.ConcreteModel()

    # Sets
    num_patterns = 12
    num_widths = 4
    model.P = pyo.RangeSet(0, num_patterns - 1)  # patterns 0..11
    model.W = pyo.RangeSet(0, num_widths - 1)   # widths 0..3

    # Variables: integer number of times each pattern is used
    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers, bounds=(0, None))

    # Objective: minimize total rolls cut
    model.obj = pyo.Objective(expr=sum(model.x[p] for p in model.P), sense=pyo.minimize)

    # Demand constraints: for each width, total yield >= demand
    def demand_rule(model, w):
        return sum(pattern_yields[p][w] * model.x[p] for p in model.P) >= demands[w]
    model.demand_constr = pyo.Constraint(model.W, rule=demand_rule)

    # Pattern usage limits
    def limit_rule(model, p):
        return model.x[p] <= pattern_limits[p]
    model.limit_constr = pyo.Constraint(model.P, rule=limit_rule)

    # Solve
    try:
        from pyomo.contrib.appsi.solvers.highs import Highs
        solver = Highs()
        results = solver.solve(model)
    except Exception as e:
        return {"objective": None, "status": f"solver_error: {str(e)}"}

    # Check if solution was found and objective value is retrievable
    try:
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except (ValueError, TypeError):
        # Try to detect infeasibility via solver status if possible
        if hasattr(results, 'solver') and hasattr(results.solver, 'status'):
            if results.solver.status == pyo.SolverStatus.warning:
                return {"objective": None, "status": "infeasible"}
        return {"objective": None, "status": "no_solution"}
```

## Program B-structured

```python
# {"sets":{"P":[0,1,2,3,4,5,6,7,8,9,10,11],"W":[0,1,2,3]},"params":{"demands":"list[4] or dict W->nonnegative int","pattern_limits":"list[12] or dict P->nonnegative int","pattern_yields":"12x4 list or dict (P,W)->nonnegative int"},"vars":{"x":"integer >= 0 for each p in P"},"constraints":["for each w in W: sum_{p in P} pattern_yields[p,w] * x[p] >= demands[w]","for each p in P: x[p] <= pattern_limits[p]"],"objective":"minimize sum_{p in P} x[p]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 11)
    model.W = pyo.RangeSet(0, 3)

    demands_data = params["demands"]
    limits_data = params["pattern_limits"]
    yields_data = params["pattern_yields"]

    def demand_init(model, w):
        return demands_data[w]

    def limit_init(model, p):
        return limits_data[p]

    def yield_init(model, p, w):
        if isinstance(yields_data, dict):
            return yields_data[(p, w)]
        return yields_data[p][w]

    model.demand = pyo.Param(
        model.W,
        initialize=demand_init,
        within=pyo.NonNegativeIntegers,
    )
    model.pattern_limit = pyo.Param(
        model.P,
        initialize=limit_init,
        within=pyo.NonNegativeIntegers,
    )
    model.yield_amt = pyo.Param(
        model.P,
        model.W,
        initialize=yield_init,
        within=pyo.NonNegativeIntegers,
        default=0,
    )

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    def demand_rule(model, w):
        return sum(model.yield_amt[p, w] * model.x[p] for p in model.P) >= model.demand[w]

    model.demand_con = pyo.Constraint(model.W, rule=demand_rule)

    def limit_rule(model, p):
        return model.x[p] <= model.pattern_limit[p]

    model.limit_con = pyo.Constraint(model.P, rule=limit_rule)

    model.obj = pyo.Objective(
        expr=sum(model.x[p] for p in model.P),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "failed"}
```

## Program C-direct

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demands = params["demands"]
    pattern_limits = params["pattern_limits"]
    pattern_yields = params["pattern_yields"]
    
    num_patterns = len(pattern_limits)
    num_widths = len(demands)
    
    model = gp.Model("cutting_stock")
    model.Params.OutputFlag = 0
    
    # Decision variables: number of times each pattern is used
    x = model.addVars(num_patterns, vtype=GRB.INTEGER, lb=0, name="x")
    
    # Objective: minimize total number of rolls cut
    model.setObjective(gp.quicksum(x[p] for p in range(num_patterns)), GRB.MINIMIZE)
    
    # Constraints: meet demand for each width
    for w in range(num_widths):
        model.addConstr(
            gp.quicksum(pattern_yields[p][w] * x[p] for p in range(num_patterns)) >= demands[w],
            name=f"demand_{w}"
        )
    
    # Constraints: respect pattern usage limits
    for p in range(num_patterns):
        model.addConstr(x[p] <= pattern_limits[p], name=f"limit_{p}")
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

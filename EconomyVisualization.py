import mesa

from mesa.visualization.modules import CanvasGrid
from mesa.visualization.modules import ChartModule
#from mesa.visualization.modules import TextElement
from mesa.visualization.ModularVisualization import ModularServer
#from mesa.visualization.TextVisualization import TextData
#from mesa.visualization.TextVisualization import TextVisualization

from EconomyModel import EconomyModel

economy_scale = 25

def agent_portrayal(agent):
    portrayal = {
        "Shape": "circle",
        "Filled": "true",
        "r": 1
    }

    if agent.token_wealth > 1000:
        portrayal["Color"] = "#f441f4"
        portrayal["Layer"] = 0
        portrayal["r"] = 0.8
    elif agent.token_wealth > 900:
        portrayal["Color"] = "#d966ff"
        portrayal["Layer"] = 0
        portrayal["r"] = 1
    elif agent.token_wealth > 800:
        portrayal["Color"] = "#8c66ff"
        portrayal["Layer"] = 0
        portrayal["r"] = 0.9
    elif agent.token_wealth > 700:
        portrayal["Color"] = "#668cff"
        portrayal["Layer"] = 0
        portrayal["r"] = 0.8
    elif agent.token_wealth > 600:
        portrayal["Color"] = "#66b3ff"
        portrayal["Layer"] = 0
        portrayal["r"] = 0.7
    elif agent.token_wealth > 500:
        portrayal["Color"] = "#66d9ff"
        portrayal["Layer"] = 0
        portrayal["r"] = 0.6
    elif agent.token_wealth > 400:
        portrayal["Color"] = "#66ffd9"
        portrayal["Layer"] = 0
        portrayal["r"] = 0.5
    elif agent.token_wealth > 300:
        portrayal["Color"] = "#66ff66"
        portrayal["Layer"] = 0
        portrayal["r"] = 0.4
    elif agent.token_wealth > 200:
        portrayal["Color"] = "#b3ff66"
        portrayal["Layer"] = 0
        portrayal["r"] = 0.3
    elif agent.token_wealth > 100:
        portrayal["Color"] = "#ffff66"
        portrayal["Layer"] = 0
        portrayal["r"] = 0.2
    elif agent.token_wealth > 0:
        portrayal["Color"] = "#ffd966"
        portrayal["Layer"] = 1
        portrayal["r"] = 0.1
    else:
        portrayal["Color"] = "#ff8c66"
        portrayal["Layer"] = 2
        portrayal["r"] = 0.0

    return portrayal

grid = CanvasGrid(agent_portrayal, economy_scale, economy_scale, 650, 650)

chart = ChartModule([
    {"Label": "Gini", "Color": "#6aa35e"}],
    data_collector_name='datacollector',
    canvas_height=600, canvas_width=550
)
#text = TextElement(js_code="document.write(5 + 6);")

server = ModularServer(EconomyModel, [grid, chart], "Economy Model", { "num_agents" : 1425, "width" : economy_scale, "height" : economy_scale} )
server.port = 8521
server.launch()

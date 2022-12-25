import random, math, numpy as np

from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import SingleGrid, MultiGrid
from mesa.datacollection import DataCollector

# global variables
assurance_incentive_pool = 0
transaction_incentive_pool = 0
economy_token_wealth = 1
asset_mean = 500
asset_stdev = 100
fraction_to_reward = 20 # one in this many agents to reward for assuring ownership
liquidity_providers_incentive_pool = 0


def assurance_incentive_gini(model):
    agent_assurance_incentive = [agent.assurance_incentive for agent in model.schedule.agents]
    x = sorted(agent_assurance_incentive)
    N = model.num_agents
    B = sum(xi * (N - i) for i, xi in enumerate(x)) / (N * sum(x))
    return 1 + (1 / N) - 2 * B


def get_revenue(model):
    return model.protocol_revenue


def get_model_assurance_probability(model):
    return model.model_assurace_probability


class EconomyModel(Model):

    global assurance_incentive_pool, protocol_revenue

    def __init__(self, num_agents, height, width, liquidityPoolModel):
        self.num_agents = num_agents
        self.running = True
        self.grid = MultiGrid(height, width, True)
        self.schedule = RandomActivation(self)
        self.model_assurace_probability = 0
        self.model_assurace_probabilities = list()
        self.protocol_revenue = 0
        self.unlock_reserve = 0
        self.datacollector = DataCollector(
            model_reporters = {"Protocol revenue": get_revenue},
            agent_reporters = {"Assurance_probability": "assurance_probability"}
        )
        self.myLiquidityPool = liquidityPoolModel
        #self.datacollector = DataCollector(model_reporters = {"Model assurance probability": get_model_assurance_probability
        #    }, agent_reporters = {"Assurance probability": "assurance_probability"})

        # create agents
        for agent_index in range(self.num_agents):
            agent = AgentModel(agent_index, self)
            self.schedule.add(agent)

            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            try:
                self.grid.place_agent(agent, (x, y))
            except Exception:
                self.grid.place_agent(agent, self.grid.find_empty)
        
        self.update_model_assurace_probability()
    

    def update_model_assurace_probability(self):
        sum = 0
        for agent in self.schedule.agents:
            sum += agent.assurance_probability
        self.model_assurace_probability = sum / self.num_agents
        self.model_assurace_probabilities.append(self.model_assurace_probability)


    # grow agent population according to Bass diffusion model, compare different models
    def grow(self):
        pass


    def execute_model(self, n):
        for i in range(n):
            self.step()
        model_assurace_probabilities = economyModel.datacollector.get_model_vars_dataframe()
        protocol_revenue = economyModel.datacollector.get_model_vars_dataframe()
        model_assurace_probabilities.plot()
        
        print(f"\nRewarded assured fraction is one in {fraction_to_reward} agents who assured asset in last 30-day period.")
        print(f"Number of agents in network is {self.num_agents} \n")


    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()
        self.update_model_assurace_probability()
        #for model_assurace_probability in self.model_assurace_probabilities:
        #    print(f"Model assurance probability is {model_assurace_probability} \n")
        #print(f"Model assurance probability is {self.model_assurace_probability} ")
        #print(f"Assurance incentive pool: {assurance_incentive_pool}")
        #print(f"Protocol reveue: {get_revenue(self)}")



class AgentModel(Agent):

    global asset_mean
    global asset_stdev

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

        global assurance_incentive_pool, transaction_incentive_pool, economy_token_wealth, fraction_to_reward, liquidity_providers_incentive_pool

        self.asset_wealth = np.random.normal(asset_mean, asset_stdev)
        self.model.unlock_reserve += self.asset_wealth # mint same number of UNLOCK as price of the asset
        self.token_wealth = (1.0-0.3-0.075) * self.asset_wealth # @IMPLEMENT: handle decimal precision
        economy_token_wealth += self.token_wealth
        self.model.protocol_revenue += 0.3 * self.asset_wealth
        assurance_incentive_pool += 0.025 * self.asset_wealth
        transaction_incentive_pool += 0.025 * self.asset_wealth
        liquidity_providers_incentive_pool += 0.025 * self.asset_wealth

        self.has_transacted = False
        self.assurance_incentive = assurance_incentive_pool * (self.token_wealth / economy_token_wealth)
        self.transaction_incentive = transaction_incentive_pool * (self.token_wealth / economy_token_wealth)

        self.assurance_probability = np.random.normal(0.65, 0.1) # when we start, we assume agents who have just joined the network are more than indifferent (>50%)
        while (self.assurance_probability < 0 or self.assurance_probability > 1):
            self.assurance_probability = np.random.normal(0.65, 0.1)
        self.model_assurace_probability = self.model.model_assurace_probability


    # subsequent tokenization of assets after the first
    # ASSUMPTION: dependent on the utility of UNLOCK, which is dependent on its price stability, which is dependent on liquidity
    def tokenize(self, liquidityPoolModel):
        # the likelihood of subsequent tokenization depends on: activity in the network

        asset_value = np.random.normal(asset_mean, asset_stdev)
        UNLOCK_value = (1.0-0.3-0.075) * self.asset_wealth
        liquidity_confidence_score = UNLOCK_value / liquidityPoolModel.UNLOCK_volume

        if self.assurance_probability * self.model.model_assurace_probability > 0.5 and liquidity_confidence_score > 0.001: 

            global assurance_incentive_pool, transaction_incentive_pool, economy_token_wealth, fraction_to_reward, liquidity_providers_incentive_pool
        
            self.asset_wealth += asset_value
            self.model.unlock_reserve += self.asset_wealth
            self.token_wealth += (1.0-0.3-0.075) * self.asset_wealth
            economy_token_wealth += self.token_wealth
            self.model.protocol_revenue += 0.3 * self.asset_wealth
            assurance_incentive_pool += 0.025 * self.asset_wealth
            transaction_incentive_pool += 0.025 * self.asset_wealth
            liquidity_providers_incentive_pool += 0.025 * self.asset_wealth

 
    def evaluate_incentive(self, model_assurace_probability, frac):
        if random.randint(1, 10000) in range(1, int(model_assurace_probability*10000)): # if assured

            if random.randint(1,frac) == 1: # if rewarded
                self.token_wealth += self.assurance_incentive
                self.update_assurance_probability_recursive(self.assurance_incentive, -14) 
            else: # if not rewarded for assurance
                self.assurance_probability *= 0.98 # because assured but was not rewarded. Express in sigmoid func terms
    
        if self.has_transacted: # @ASSUMPTION: everyone who transacted getting incentive, as opposed to assurance
            self.token_wealth += self.transaction_incentive

            
    def move(self):
        pass

    
    def transact(self):
        self.has_transacted = True

        
    def update_assurance_probability_sigmoidal(self, incentive):
        self.assurance_probability = 0.1 + (0.9 / 1 + math.exp(-1 * incentive)) # @IMPLEMENT step count k to mimic x along x-axis

        
    # using the sigmoid function because reaction is not linear: getting 100 times more incentive does not means you are 100 times more likely to act i.e. plateaus
    def update_assurance_probability_recursive(self, incentive, β):
        self.assurance_probability += (1 - self.assurance_probability) * (1 / (1 + math.exp(-1 * (incentive) )))

        
    # def non_incentivization_effect(self): move effect here for more detail            

    def step(self):
        self.evaluate_incentive(self.model.model_assurace_probability, fraction_to_reward) # more like dis/incentivize
        self.tokenize(self.model.myLiquidityPool)
        #print(f"Agent {self.unique_id}. Assurance probability: {self.assurance_probability}, token wealth: {self.token_wealth} \n")



class LiquidityPoolModel(Model):

    global liquidity_providers_incentive_pool

    def __init__(self, num_liquidity_providers, height, width):
        self.num_liquidity_providers = num_liquidity_providers
        self.UNLOCK_ALGO_ratio = 4  # UNLOCK per unit ALGO, appproximate given current prices (for 1 UNLOCK backed by $1)
        self.liquidity_incentive = 1
        self.schedule = RandomActivation(self)
        self.liquidity_provider_UNLOCK_mean = 100
        self.liquidity_provider_UNLOCK_variance = 20
        self.UNLOCK_volume = 100000 # initialized volumes to provide some liquidity
        self.ALGO_volume = 400000

        self.grid = MultiGrid(height, width, True)

        for liquidity_provider_id in range(num_liquidity_providers):
            liquidity_provider = LiquidityProvider(liquidity_provider_id, self)
            self.schedule.add(liquidity_provider)
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            try:
                self.grid.place_agent(liquidity_provider, (x, y))
            except Exception:
                self.grid.place_agent(liquidity_provider, self.grid.find_empty)


    def add_liquidity_providers(self, liquidity_providers_incentive_pool):
        pass


    def take_liquidity(self, UNLOCK_ALGO_pair):
        if self.model.schedule.steps == 1:        
            self.UNLOCK_volume += UNLOCK_ALGO_pair[0]
            self.ALGO_volume += UNLOCK_ALGO_pair[1]
            for agent in self.schedule.agents:
                agent.provide_liquidity()

        for agent in self.schedule.agents:
            agent.add_liquidity()

    
    def reward_liquidity_providers(self):
        incentive_pool = liquidity_providers_incentive_pool

        for liquidity_provider in self.schedule.agents:
            reward_fraction = liquidity_provider.UNLOCK_volume / self.UNLOCK_volume
            reward_value = incentive_pool * reward_fraction
            liquidity_provider.accept_reward(reward_value)


            
class LiquidityProvider(Agent):

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.UNLOCK_volume = np.random.normal(self.model.liquidity_provider_UNLOCK_mean, self.model.liquidity_provider_UNLOCK_variance)
        self.ALGO_volume = self.model.UNLOCK_ALGO_ratio * self.UNLOCK_volume
        self.UNLOCK_reward = 0


    def provide_liquidity(self):
        if self.model.schedule.steps == 1:
            self.model.take_liquidity(self.UNLOCK_volume, self.ALGO_volume)
        else:
            pass
    
    
    def add_liquidity(self):
        # make this on the condition that some requirements are met
        pass

    
    def remove_liquidity(self, fraction):
        pass

    
    def accept_reward(self, reward):
        self.UNLOCK_reward += reward

    
    def withdraw_from_pool(self):
        self.remove_liquidity(1)

    
    def step(self):
        self.provide_liquidity()



if __name__ == "__main__":

    liquidityPoolModel = LiquidityPoolModel(50, 10, 10)

    economyModel = EconomyModel(10, 10, 10, liquidityPoolModel)
    
    economyModel.execute_model(30)

    agent_assurance_probabilities = economyModel.datacollector.get_agent_vars_dataframe()
    single_agent_assurance = agent_assurance_probabilities.xs(2, level="AgentID")
    #print(agent_assurance_probabilities.head(n=40))
    #single_agent_assurance.Assurance_probability.plot()

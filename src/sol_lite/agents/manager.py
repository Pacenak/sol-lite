"""Agent manager."""
class AgentManager:
    def __init__(self, registry, models):
        self.registry = registry
        self.models = models

    def model_for_agent(self, agent_id):
        return self.models.profile(self.registry.get(agent_id).model_profile).model

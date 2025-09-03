import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional, Any
import json

class SimpleObesityNetwork:
    """
    A simplified obesity factor network with 10 key nodes.
    Implements Bayesian updates for network parameters and generates
    recommendations based on intervention potential.
    """
    
    def __init__(self):
        # Initialize the directed graph
        self.G = nx.DiGraph()
        
        # Define the 10 key factors (nodes)
        self.factors = {
            "caloric_intake": {"modifiable": 10, "baseline": 0.7, "current": 0.7, "description": "Daily caloric intake"},
            "physical_activity": {"modifiable": 9, "baseline": 0.5, "current": 0.5, "description": "Level of physical activity"},
            "sleep_quality": {"modifiable": 7, "baseline": 0.6, "current": 0.6, "description": "Quality and duration of sleep"},
            "stress_level": {"modifiable": 6, "baseline": 0.6, "current": 0.6, "description": "Level of stress (lower is better)"},
            "meal_timing": {"modifiable": 8, "baseline": 0.5, "current": 0.5, "description": "Consistency of meal timing"},
            "metabolism": {"modifiable": 2, "baseline": 0.5, "current": 0.5, "description": "Metabolic rate"},
            "hunger_hormones": {"modifiable": 3, "baseline": 0.5, "current": 0.5, "description": "Regulation of hunger hormones"},
            "weight": {"modifiable": 0, "baseline": 0.5, "current": 0.5, "description": "Current weight (target node)"},
            "food_environment": {"modifiable": 5, "baseline": 0.6, "current": 0.6, "description": "Access to healthy food options"},
            "social_support": {"modifiable": 4, "baseline": 0.4, "current": 0.4, "description": "Support from friends and family"}
        }
        
        # Add nodes to the graph
        for factor, attrs in self.factors.items():
            self.G.add_node(factor, **attrs)
        
        # Define the relationships (edges) with weights representing strength of influence
        self.relationships = [
            ("caloric_intake", "weight", 0.8),
            ("physical_activity", "weight", 0.7),
            ("physical_activity", "metabolism", 0.5),
            ("sleep_quality", "hunger_hormones", 0.6),
            ("sleep_quality", "stress_level", 0.5),
            ("stress_level", "caloric_intake", 0.4),
            ("stress_level", "sleep_quality", 0.6),
            ("meal_timing", "hunger_hormones", 0.5),
            ("meal_timing", "metabolism", 0.3),
            ("metabolism", "weight", 0.6),
            ("hunger_hormones", "caloric_intake", 0.7),
            ("food_environment", "caloric_intake", 0.6),
            ("social_support", "stress_level", 0.5),
            ("social_support", "physical_activity", 0.4)
        ]
        
        # Add edges to the graph
        for source, target, weight in self.relationships:
            self.G.add_edge(source, target, weight=weight, confidence=0.7)
    
    def update_factor(self, factor: str, value: float, confidence: float = 0.7) -> bool:
        """
        Update a factor's current value based on user input using Bayesian updating
        
        Args:
            factor: The name of the factor to update
            value: The new value (0-1 scale)
            confidence: Confidence in this measurement (0-1)
            
        Returns:
            bool: True if update was successful
        """
        if factor not in self.factors:
            return False
        
        # Bayesian update
        prior = self.factors[factor]["current"]
        prior_confidence = 0.7  # Default prior confidence
        
        # Weighted average based on confidence (Bayesian update)
        posterior = (prior * prior_confidence + value * confidence) / (prior_confidence + confidence)
        
        # Update both the factors dictionary and the graph node
        self.factors[factor]["current"] = posterior
        self.G.nodes[factor]["current"] = posterior
        
        return True
    
    def update_relationship(self, source: str, target: str, strength: float, confidence: float = 0.7) -> bool:
        """
        Update a relationship's strength based on observed data using Bayesian updating
        
        Args:
            source: Source factor
            target: Target factor
            strength: New relationship strength (0-1)
            confidence: Confidence in this update
            
        Returns:
            bool: True if update was successful
        """
        if not self.G.has_edge(source, target):
            return False
        
        # Bayesian update for edge weight
        prior_weight = self.G[source][target]["weight"]
        prior_confidence = self.G[source][target]["confidence"]
        
        # Weighted average based on confidence (Bayesian update)
        posterior_weight = (prior_weight * prior_confidence + strength * confidence) / (prior_confidence + confidence)
        
        # Increase confidence with more data, but cap at 1.0
        posterior_confidence = min(prior_confidence + confidence * 0.3, 1.0)
        
        # Update the edge attributes
        self.G[source][target]["weight"] = posterior_weight
        self.G[source][target]["confidence"] = posterior_confidence
        
        return True
    
    def calculate_intervention_potential(self) -> Dict[str, float]:
        """
        Calculate the potential impact of intervening on each factor
        
        Returns:
            Dict mapping factor names to intervention potential scores
        """
        intervention_potentials = {}
        
        for factor in self.factors:
            # Skip the target node (weight)
            if factor == "weight":
                continue
            
            # Direct effect on weight (if any)
            direct_effect = 0
            if self.G.has_edge(factor, "weight"):
                direct_effect = self.G[factor]["weight"]["weight"]
            
            # First-order indirect effects
            indirect_effect = 0
            for intermediate in self.G.successors(factor):
                if intermediate != "weight" and self.G.has_edge(intermediate, "weight"):
                    # The effect through this path is the product of the weights
                    path_effect = self.G[factor][intermediate]["weight"] * self.G[intermediate]["weight"]["weight"]
                    indirect_effect += path_effect
            
            # Second-order indirect effects (through two intermediate nodes)
            second_order_effect = 0
            for intermediate1 in self.G.successors(factor):
                if intermediate1 != "weight":
                    for intermediate2 in self.G.successors(intermediate1):
                        if intermediate2 != "weight" and self.G.has_edge(intermediate2, "weight"):
                            # The effect through this path is the product of the weights
                            path_effect = (self.G[factor][intermediate1]["weight"] * 
                                          self.G[intermediate1][intermediate2]["weight"] * 
                                          self.G[intermediate2]["weight"]["weight"])
                            second_order_effect += path_effect
            
            # Total effect combines direct and indirect (with indirect discounted)
            total_effect = direct_effect + 0.5 * indirect_effect + 0.25 * second_order_effect
            
            # Modifiability from node attributes
            modifiability = self.G.nodes[factor]["modifiable"] / 10.0  # Scale to 0-1
            
            # Intervention potential combines effect size with modifiability
            intervention_potentials[factor] = total_effect * modifiability
        
        return intervention_potentials
    
    def get_top_recommendations(self, n: int = 3) -> List[Dict]:
        """
        Get the top n recommendations based on intervention potential
        
        Args:
            n: Number of recommendations to return
            
        Returns:
            List of recommendation dictionaries
        """
        potentials = self.calculate_intervention_potential()
        
        # Sort factors by intervention potential
        sorted_factors = sorted(potentials.items(), key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for factor, potential in sorted_factors[:n]:
            # Determine if the recommendation is to increase or decrease
            # For most factors, higher values are better except for stress_level
            direction = "increase" if factor != "stress_level" else "decrease"
            
            # Get current value and description
            current_value = self.factors[factor]["current"]
            description = self.factors[factor]["description"]
            
            # Generate a recommendation
            recommendation = {
                "factor": factor,
                "description": description,
                "potential": potential,
                "current_value": current_value,
                "direction": direction,
                "confidence": min(0.5 + potential, 0.9)  # Higher potential = higher confidence
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def get_network_state(self) -> Dict[str, Any]:
        """
        Get the current state of the network
        
        Returns:
            Dict containing the current state of the network
        """
        # Get current factor values
        factors = {factor: self.factors[factor]["current"] for factor in self.factors}
        
        # Get current relationship strengths
        relationships = []
        for source, target, data in self.G.edges(data=True):
            relationships.append({
                "from": source,
                "to": target,
                "strength": data["weight"],
                "confidence": data["confidence"]
            })
        
        return {
            "factors": factors,
            "relationships": relationships
        }
    
    def set_network_state(self, state: Dict[str, Any]) -> bool:
        """
        Set the network state from a saved state
        
        Args:
            state: Dict containing the network state
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Update factor values
            for factor, value in state["factors"].items():
                if factor in self.factors:
                    self.factors[factor]["current"] = value
                    self.G.nodes[factor]["current"] = value
            
            # Update relationship strengths
            for rel in state["relationships"]:
                source = rel["from"]
                target = rel["to"]
                strength = rel["strength"]
                confidence = rel.get("confidence", 0.7)
                
                if self.G.has_edge(source, target):
                    self.G[source][target]["weight"] = strength
                    self.G[source][target]["confidence"] = confidence
            
            return True
        except Exception as e:
            print(f"Error setting network state: {e}")
            return False
    
    def visualize_network(self, highlight_recommendations: bool = True) -> plt.Figure:
        """
        Visualize the network with node sizes representing intervention potential
        
        Args:
            highlight_recommendations: Whether to highlight the top recommendations
            
        Returns:
            matplotlib Figure object
        """
        # Get positions for nodes
        pos = nx.spring_layout(self.G, seed=42)
        
        # Get intervention potentials for node sizes
        potentials = self.calculate_intervention_potential()
        potentials["weight"] = 0  # Target node has no intervention potential
        
        # Get node sizes based on intervention potential
        node_sizes = [potentials.get(node, 0) * 1000 + 300 for node in self.G.nodes()]
        
        # Get edge widths based on weights
        edge_widths = [self.G[u][v]["weight"] * 2 for u, v in self.G.edges()]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Draw the graph
        nx.draw_networkx_nodes(self.G, pos, node_size=node_sizes, node_color="skyblue", ax=ax)
        
        # Highlight top recommendations if requested
        if highlight_recommendations:
            top_recs = [r["factor"] for r in self.get_top_recommendations(3)]
            nx.draw_networkx_nodes(self.G, pos, nodelist=top_recs, node_size=node_sizes, 
                                node_color="orange", ax=ax)
        
        # Draw edges with varying widths
        nx.draw_networkx_edges(self.G, pos, width=edge_widths, edge_color="gray", 
                            alpha=0.7, ax=ax)
        
        # Draw labels
        nx.draw_networkx_labels(self.G, pos, font_size=10, ax=ax)
        
        plt.title("Obesity Factor Network")
        plt.axis("off")
        
        return fig
    
    def to_json(self) -> str:
        """
        Convert the network state to JSON
        
        Returns:
            JSON string representation of the network state
        """
        state = self.get_network_state()
        return json.dumps(state)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SimpleObesityNetwork':
        """
        Create a network from a JSON string
        
        Args:
            json_str: JSON string representation of the network state
            
        Returns:
            SimpleObesityNetwork instance
        """
        network = cls()
        state = json.loads(json_str)
        network.set_network_state(state)
        return network

# Example usage
if __name__ == "__main__":
    # Create the network
    network = SimpleObesityNetwork()
    
    # Get top recommendations
    recommendations = network.get_top_recommendations(3)
    print("Top recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['factor']} - {rec['description']} - {rec['direction']} (impact: {rec['potential']:.2f})")
    
    # Visualize the network
    fig = network.visualize_network()
    plt.show()
    
    # Example of updating based on user conversation
    print("\nUpdating based on user data...")
    network.update_factor("sleep_quality", 0.3)  # User has poor sleep
    network.update_factor("stress_level", 0.8)  # User has high stress
    
    # Get updated recommendations
    print("\nUpdated recommendations:")
    updated_recommendations = network.get_top_recommendations(3)
    for i, rec in enumerate(updated_recommendations, 1):
        print(f"{i}. {rec['factor']} - {rec['description']} - {rec['direction']} (impact: {rec['potential']:.2f})")
    
    # Save network state to JSON
    json_str = network.to_json()
    print("\nNetwork state saved to JSON")
    
    # Create a new network from JSON
    new_network = SimpleObesityNetwork.from_json(json_str)
    print("Network state restored from JSON") 
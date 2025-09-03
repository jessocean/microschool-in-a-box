import matplotlib.pyplot as plt
from simplified_obesity_network import SimpleObesityNetwork

def test_network():
    """Test the obesity network model"""
    print("Testing obesity network model...")
    
    # Create the network
    network = SimpleObesityNetwork()
    
    # Get initial recommendations
    print("\nInitial recommendations:")
    recommendations = network.get_top_recommendations(3)
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['factor']} - {rec['description']} - {rec['direction']} (impact: {rec['potential']:.2f})")
    
    # Visualize the network
    print("\nGenerating network visualization...")
    fig = network.visualize_network()
    plt.savefig("network_visualization.png")
    print("Visualization saved to network_visualization.png")
    
    # Update based on user data
    print("\nUpdating based on user data...")
    network.update_factor("sleep_quality", 0.3)  # User has poor sleep
    network.update_factor("stress_level", 0.8)  # User has high stress
    network.update_factor("physical_activity", 0.4)  # User has low physical activity
    
    # Get updated recommendations
    print("\nUpdated recommendations:")
    updated_recommendations = network.get_top_recommendations(3)
    for i, rec in enumerate(updated_recommendations, 1):
        print(f"{i}. {rec['factor']} - {rec['description']} - {rec['direction']} (impact: {rec['potential']:.2f})")
    
    # Test network state serialization
    print("\nTesting network state serialization...")
    json_str = network.to_json()
    print("Network state saved to JSON")
    
    # Create a new network from JSON
    new_network = SimpleObesityNetwork.from_json(json_str)
    print("Network state restored from JSON")
    
    # Verify the new network has the same recommendations
    print("\nVerifying restored network...")
    restored_recommendations = new_network.get_top_recommendations(3)
    for i, rec in enumerate(restored_recommendations, 1):
        print(f"{i}. {rec['factor']} - {rec['description']} - {rec['direction']} (impact: {rec['potential']:.2f})")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_network() 
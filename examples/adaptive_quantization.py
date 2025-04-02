#!/usr/bin/env python3
"""
Adaptive Quantization example using Reflexia Model Manager
This demonstrates the dynamic quantization feature based on content complexity and memory pressure.
"""

import os
import sys
import time

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from model_manager import ModelManager
from memory_manager import MemoryManager

# Example prompts of varying complexity
SIMPLE_PROMPT = "What's the capital of France?"

MEDIUM_PROMPT = """
Explain the differences between supervised and unsupervised learning in machine learning.
Provide some examples of algorithms that fall into each category.
"""

COMPLEX_PROMPT = """
Analyze the following quantum computing code for potential optimization:

```python
from qiskit import QuantumCircuit, Aer, execute
from qiskit.visualization import plot_histogram
import numpy as np

# Create a quantum circuit with 3 qubits
qc = QuantumCircuit(3)

# Apply H-gate to the first qubit
qc.h(0)

# Apply CNOT gate with control=first qubit and target=second qubit
qc.cx(0, 1)

# Apply CNOT gate with control=first qubit and target=third qubit
qc.cx(0, 2)

# Measure all qubits
qc.measure_all()

# Execute the circuit on the qasm simulator
simulator = Aer.get_backend('qasm_simulator')
job = execute(qc, simulator, shots=1000)
result = job.result()

# Get the histogram data
counts = result.get_counts(qc)
print(counts)
```

Explain the quantum state at each step and identify any possible inefficiencies or improvements.
"""

def main():
    """Run an adaptive quantization example"""
    print("Reflexia Model Manager - Adaptive Quantization Example")
    print("-" * 50)
    
    # Initialize configuration
    config = Config()
    config.set("model", "name", "reflexia-r1")
    config.set("model", "quantization", "q4_0")  # Start with lowest quantization
    config.set("model", "context_length", 4096)
    
    # Create managers
    print("Initializing managers...")
    model_manager = ModelManager(config)
    memory_manager = MemoryManager(config, model_manager)
    
    # Display initial quantization
    print(f"Initial quantization: {model_manager.quantization}")
    
    # Process prompts from simple to complex
    prompts = [
        ("Simple", SIMPLE_PROMPT),
        ("Medium", MEDIUM_PROMPT),
        ("Complex", COMPLEX_PROMPT),
    ]
    
    for complexity, prompt in prompts:
        print(f"\n\n{'=' * 30}")
        print(f"Processing {complexity} Prompt")
        print(f"{'=' * 30}")
        
        # Estimate complexity
        content_complexity = model_manager.estimate_content_complexity(prompt)
        print(f"Estimated complexity: {content_complexity:.2f}")
        
        # Adapt quantization
        changed = model_manager.adaptive_quantization(
            memory_manager=memory_manager, 
            content_complexity=content_complexity
        )
        
        if changed:
            print(f"Quantization adapted to: {model_manager.quantization}")
        else:
            print(f"Quantization unchanged: {model_manager.quantization}")
            
        # Generate response with timing
        print("\nGenerating response...")
        start_time = time.time()
        
        response = model_manager.generate_response(
            prompt=prompt,
            temperature=0.7,
            top_p=0.9
        )
        
        elapsed = time.time() - start_time
        
        # Show summary
        print(f"\nResponse generated in {elapsed:.2f} seconds")
        print(f"Response length: {len(response)} characters")
        
        # Show memory usage
        memory_stats = memory_manager.get_memory_stats()
        print(f"Memory usage: {memory_stats['percent']}%")
        
        # Wait before next prompt to let system stabilize
        if complexity != "Complex":
            print("\nWaiting for system to stabilize before next prompt...")
            time.sleep(5)
    
    print("\nExample complete!")

if __name__ == "__main__":
    main()